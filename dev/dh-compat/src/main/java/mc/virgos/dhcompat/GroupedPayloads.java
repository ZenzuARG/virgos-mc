package mc.virgos.dhcompat;

import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayload;
import mc.virgos.dhcompat.mixin.FullDataPayloadIdAccessor;

import java.util.Objects;
import java.util.concurrent.atomic.AtomicInteger;

/** Per-response metadata ownership; the native immutable encoded payload stays shared. */
public final class GroupedPayloads {
    private GroupedPayloads() {}

    public static FullDataPayload forResponse(FullDataPayload encoded) {
        return withNativeId(encoded, FullDataPayloadIdAccessor.virgos$lastBufferId());
    }

    static FullDataPayload withNativeId(FullDataPayload encoded, AtomicInteger nativeIds) {
        Objects.requireNonNull(encoded, "Encoded grouped payload");
        Objects.requireNonNull(encoded.dtoBuffer, "Encoded grouped buffer");
        var response = new FullDataPayload();
        response.dtoBufferId = nativeIds.getAndIncrement();
        response.dtoBuffer = encoded.dtoBuffer;
        response.beaconBeams = encoded.beaconBeams;
        return response;
    }
}
