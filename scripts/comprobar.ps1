param(
    [string]$Address = '127.0.0.1',
    [ValidateRange(1, 65535)][int]$Port = 25565
)
$ErrorActionPreference = 'Stop'

# Minecraft Server List Ping: tests the game protocol, not just an open port.
function ConvertTo-VarInt([int]$Value) {
    $bytes = New-Object 'System.Collections.Generic.List[byte]'
    do {
        $part = $Value -band 127
        $Value = $Value -shr 7
        if ($Value -ne 0) { $part = $part -bor 128 }
        $bytes.Add([byte]$part)
    } while ($Value -ne 0)
    return $bytes.ToArray()
}

function Read-VarInt([System.IO.Stream]$Stream) {
    $value = 0
    for ($i = 0; $i -lt 5; $i++) {
        $part = $Stream.ReadByte()
        if ($part -lt 0) { throw 'El servidor cerro la conexion.' }
        $value = $value -bor (($part -band 127) -shl (7 * $i))
        if (($part -band 128) -eq 0) { return $value }
    }
    throw 'Respuesta invalida: VarInt demasiado largo.'
}

function Read-Bytes([System.IO.Stream]$Stream, [int]$Count) {
    if ($Count -lt 0 -or $Count -gt 1048576) { throw 'Respuesta demasiado grande o invalida.' }
    $buffer = New-Object byte[] $Count
    $offset = 0
    while ($offset -lt $Count) {
        $read = $Stream.Read($buffer, $offset, $Count - $offset)
        if ($read -eq 0) { throw 'Respuesta incompleta del servidor.' }
        $offset += $read
    }
    return ,$buffer
}

$client = New-Object System.Net.Sockets.TcpClient
try {
    $connectAddress = $Address
    $parsedIP = $null
    if (-not $PSBoundParameters.ContainsKey('Port') -and -not [Net.IPAddress]::TryParse($Address, [ref]$parsedIP) -and $Address -ne 'localhost') {
        $srv = Resolve-DnsName -Name "_minecraft._tcp.$Address" -Type SRV -ErrorAction SilentlyContinue |
            Where-Object Type -eq SRV | Sort-Object Priority | Select-Object -First 1
        if ($srv) { $connectAddress = $srv.NameTarget; $Port = $srv.Port }
    }
    $connection = $client.ConnectAsync($connectAddress, $Port)
    if (-not $connection.Wait(5000)) { throw "No responde ${Address}:$Port. Inicia el servidor primero." }
    $stream = $client.GetStream()
    $stream.ReadTimeout = 5000
    $stream.WriteTimeout = 5000
    $addressBytes = [Text.Encoding]::UTF8.GetBytes($Address)
    if ($addressBytes.Length -gt 255) { throw 'Direccion demasiado larga.' }
    [byte[]]$handshake = @(0) + @(ConvertTo-VarInt 763) + @(ConvertTo-VarInt $addressBytes.Length) + $addressBytes + @([byte]($Port -shr 8), [byte]($Port -band 255), 1)
    [byte[]]$request = @(ConvertTo-VarInt $handshake.Length) + $handshake + @(1, 0)
    $stream.Write($request, 0, $request.Length)
    $packetLength = Read-VarInt $stream
    $packet = New-Object System.IO.MemoryStream(,(Read-Bytes $stream $packetLength))
    try {
        if ((Read-VarInt $packet) -ne 0) { throw 'El servidor no devolvio un paquete de estado.' }
        $jsonLength = Read-VarInt $packet
        $status = [Text.Encoding]::UTF8.GetString((Read-Bytes $packet $jsonLength)) | ConvertFrom-Json
    } finally { $packet.Dispose() }
    if ($status.version.protocol -ne 763) { throw "El servidor responde, pero su version no es Minecraft 1.20/1.20.1: $($status.version.name)" }
    [ordered]@{
        result = 'OK'
        address = "${Address}:$Port"
        version = $status.version.name
        protocol = $status.version.protocol
        players = "$($status.players.online)/$($status.players.max)"
        description = $status.description
    } | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Comprobacion fallida: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    $client.Dispose()
}

