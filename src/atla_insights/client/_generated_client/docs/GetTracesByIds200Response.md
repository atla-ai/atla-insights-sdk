# GetTracesByIds200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**traces** | [**List[GetTracesByIds200ResponseTracesInner]**](GetTracesByIds200ResponseTracesInner.md) |  | 

## Example

```python
from _generated_client.models.get_traces_by_ids200_response import GetTracesByIds200Response

# TODO update the JSON string below
json = "{}"
# create an instance of GetTracesByIds200Response from a JSON string
get_traces_by_ids200_response_instance = GetTracesByIds200Response.from_json(json)
# print the JSON string representation of the object
print(GetTracesByIds200Response.to_json())

# convert the object into a dict
get_traces_by_ids200_response_dict = get_traces_by_ids200_response_instance.to_dict()
# create an instance of GetTracesByIds200Response from a dict
get_traces_by_ids200_response_from_dict = GetTracesByIds200Response.from_dict(get_traces_by_ids200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


