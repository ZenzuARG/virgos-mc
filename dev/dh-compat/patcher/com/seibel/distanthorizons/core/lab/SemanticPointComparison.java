package com.seibel.distanthorizons.core.lab;
import com.seibel.distanthorizons.core.dataObjects.fullData.sources.FullDataSourceV2;
import com.seibel.distanthorizons.core.util.FullDataPointUtil;
/** Version-pinned semantic palette comparison for Distant Horizons 3.3.3. */
public final class SemanticPointComparison {
 private SemanticPointComparison() {}
 public static int compare(FullDataSourceV2 existing,int[] remapping,long previous,long incoming){
  long mapped=FullDataPointUtil.remap(remapping,incoming);
  if(previous==mapped)return 0;
  if(((previous^mapped)&~FullDataPointUtil.ID_MASK)!=0)return 1;
  int oldId=FullDataPointUtil.getId(previous),newId=FullDataPointUtil.getId(mapped);
  var map=existing.mapping;
  return map.getBlockStateWrapper(oldId).getSerialString().equals(map.getBlockStateWrapper(newId).getSerialString())
   &&map.getBiomeWrapper(oldId).getSerialString().equals(map.getBiomeWrapper(newId).getSerialString())?0:1;
 }
}
