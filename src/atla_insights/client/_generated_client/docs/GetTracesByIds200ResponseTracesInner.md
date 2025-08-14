# GetTracesByIds200ResponseTracesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**environment** | **str** |  | 
**is_success** | **bool** |  | 
**is_completed** | **bool** |  | 
**metadata** | **Dict[str, str]** |  | [optional] 
**step_count** | **int** |  | 
**started_at** | **str** |  | 
**ended_at** | **str** |  | 
**duration_seconds** | **float** |  | 
**ingested_at** | **str** |  | 
**spans** | [**List[GetTracesByIds200ResponseTracesInnerSpansInner]**](GetTracesByIds200ResponseTracesInnerSpansInner.md) |  | [optional] 
**custom_metric_values** | [**List[GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner]**](GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner.md) |  | [optional] 

## Example

```python
from _generated_client.models.get_traces_by_ids200_response_traces_inner import GetTracesByIds200ResponseTracesInner

# TODO update the JSON string below
json = "{}"
# create an instance of GetTracesByIds200ResponseTracesInner from a JSON string
get_traces_by_ids200_response_traces_inner_instance = GetTracesByIds200ResponseTracesInner.from_json(json)
# print the JSON string representation of the object
print(GetTracesByIds200ResponseTracesInner.to_json())

# convert the object into a dict
get_traces_by_ids200_response_traces_inner_dict = get_traces_by_ids200_response_traces_inner_instance.to_dict()
# create an instance of GetTracesByIds200ResponseTracesInner from a dict
get_traces_by_ids200_response_traces_inner_from_dict = GetTracesByIds200ResponseTracesInner.from_dict(get_traces_by_ids200_response_traces_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


