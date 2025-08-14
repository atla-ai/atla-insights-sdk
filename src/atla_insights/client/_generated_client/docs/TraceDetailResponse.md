# TraceDetailResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**trace** | [**TraceWithDetails**](TraceWithDetails.md) |  | 

## Example

```python
from _generated_client.models.trace_detail_response import TraceDetailResponse

# TODO update the JSON string below
json = "{}"
# create an instance of TraceDetailResponse from a JSON string
trace_detail_response_instance = TraceDetailResponse.from_json(json)
# print the JSON string representation of the object
print(TraceDetailResponse.to_json())

# convert the object into a dict
trace_detail_response_dict = trace_detail_response_instance.to_dict()
# create an instance of TraceDetailResponse from a dict
trace_detail_response_from_dict = TraceDetailResponse.from_dict(trace_detail_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


