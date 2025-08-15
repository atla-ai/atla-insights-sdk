# DetailedTraceListResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**traces** | [**List[TraceWithDetails]**](TraceWithDetails.md) |  | 

## Example

```python
from _generated_client.models.detailed_trace_list_response import DetailedTraceListResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DetailedTraceListResponse from a JSON string
detailed_trace_list_response_instance = DetailedTraceListResponse.from_json(json)
# print the JSON string representation of the object
print(DetailedTraceListResponse.to_json())

# convert the object into a dict
detailed_trace_list_response_dict = detailed_trace_list_response_instance.to_dict()
# create an instance of DetailedTraceListResponse from a dict
detailed_trace_list_response_from_dict = DetailedTraceListResponse.from_dict(detailed_trace_list_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


