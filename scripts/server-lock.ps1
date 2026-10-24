function Enter-ServerLock([string]$Root,[string]$Kind='server') {
    $file=Join-Path $Root '.runtime/server-control.lock'
    [void][IO.Directory]::CreateDirectory((Split-Path -Parent $file))
    $nonce=[Guid]::NewGuid().ToString()
    for($attempt=0;$attempt -lt 2;$attempt++) {
        try {$stream=[IO.File]::Open($file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)} catch [IO.IOException] {
            if(-not (Test-Path -LiteralPath $file)) {throw}
            try {$old=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json} catch {throw 'Otra operacion esta iniciando. Reintenta en unos segundos.'}
            if(-not $old.pid -or (Get-Process -Id $old.pid -ErrorAction SilentlyContinue)) {throw 'Ya hay un arranque, servidor o respaldo en curso.'}
            Remove-Item -LiteralPath $file
            continue
        }
        try {
            $data=[Text.Encoding]::UTF8.GetBytes((@{pid=$PID;nonce=$nonce;kind=$Kind;created=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress))
            $stream.Write($data,0,$data.Length)
        } finally {$stream.Dispose()}
        return @{file=$file;nonce=$nonce}
    }
    throw 'No se pudo reservar el control del servidor.'
}
function Exit-ServerLock($Lease) {
    if($Lease -and (Test-Path -LiteralPath $Lease.file)) {
        $current=Get-Content -LiteralPath $Lease.file -Raw | ConvertFrom-Json
        if($current.nonce -eq $Lease.nonce) {Remove-Item -LiteralPath $Lease.file}
    }
}
