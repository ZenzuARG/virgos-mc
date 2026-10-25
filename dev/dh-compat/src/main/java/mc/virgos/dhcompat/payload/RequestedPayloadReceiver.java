package mc.virgos.dhcompat.payload;

import com.seibel.distanthorizons.core.multiplayer.fullData.FullDataPayload;

/** Internal addon bridge implemented only on the client receiver. */
public interface RequestedPayloadReceiver {
    Runnable virgos$claim(FullDataPayload payload);
}
