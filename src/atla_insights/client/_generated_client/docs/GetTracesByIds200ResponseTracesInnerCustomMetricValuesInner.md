# GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**trace_id** | **str** |  | 
**custom_metric_id** | **str** |  | 
**value** | **str** |  | 
**custom_metric** | [**GetTracesByIds200ResponseTracesInnerCustomMetricValuesInnerCustomMetric**](GetTracesByIds200ResponseTracesInnerCustomMetricValuesInnerCustomMetric.md) |  | [optional] 

## Example

```python
from _generated_client.models.get_traces_by_ids200_response_traces_inner_custom_metric_values_inner import GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner

# TODO update the JSON string below
json = "{}"
# create an instance of GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner from a JSON string
get_traces_by_ids200_response_traces_inner_custom_metric_values_inner_instance = GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner.from_json(json)
# print the JSON string representation of the object
print(GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner.to_json())

# convert the object into a dict
get_traces_by_ids200_response_traces_inner_custom_metric_values_inner_dict = get_traces_by_ids200_response_traces_inner_custom_metric_values_inner_instance.to_dict()
# create an instance of GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner from a dict
get_traces_by_ids200_response_traces_inner_custom_metric_values_inner_from_dict = GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner.from_dict(get_traces_by_ids200_response_traces_inner_custom_metric_values_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


