# GetTracesByIds200ResponseTracesInnerSpansInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**trace_id** | **str** |  | 
**parent_span_id** | **str** |  | 
**span_name** | **str** |  | 
**start_timestamp** | **str** |  | 
**end_timestamp** | **str** |  | 
**is_exception** | **bool** |  | 
**otel_events** | **List[object]** |  | 
**annotations** | [**List[GetTracesByIds200ResponseTracesInnerSpansInnerAnnotationsInner]**](GetTracesByIds200ResponseTracesInnerSpansInnerAnnotationsInner.md) |  | [optional] 

## Example

```python
from _generated_client.models.get_traces_by_ids200_response_traces_inner_spans_inner import GetTracesByIds200ResponseTracesInnerSpansInner

# TODO update the JSON string below
json = "{}"
# create an instance of GetTracesByIds200ResponseTracesInnerSpansInner from a JSON string
get_traces_by_ids200_response_traces_inner_spans_inner_instance = GetTracesByIds200ResponseTracesInnerSpansInner.from_json(json)
# print the JSON string representation of the object
print(GetTracesByIds200ResponseTracesInnerSpansInner.to_json())

# convert the object into a dict
get_traces_by_ids200_response_traces_inner_spans_inner_dict = get_traces_by_ids200_response_traces_inner_spans_inner_instance.to_dict()
# create an instance of GetTracesByIds200ResponseTracesInnerSpansInner from a dict
get_traces_by_ids200_response_traces_inner_spans_inner_from_dict = GetTracesByIds200ResponseTracesInnerSpansInner.from_dict(get_traces_by_ids200_response_traces_inner_spans_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


