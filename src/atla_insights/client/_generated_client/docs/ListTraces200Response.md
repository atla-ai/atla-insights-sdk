# ListTraces200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**traces** | [**List[ListTraces200ResponseTracesInner]**](ListTraces200ResponseTracesInner.md) |  | 
**total** | **float** |  | 
**page** | **int** |  | 
**page_size** | **int** |  | 

## Example

```python
from _generated_client.models.list_traces200_response import ListTraces200Response

# TODO update the JSON string below
json = "{}"
# create an instance of ListTraces200Response from a JSON string
list_traces200_response_instance = ListTraces200Response.from_json(json)
# print the JSON string representation of the object
print(ListTraces200Response.to_json())

# convert the object into a dict
list_traces200_response_dict = list_traces200_response_instance.to_dict()
# create an instance of ListTraces200Response from a dict
list_traces200_response_from_dict = ListTraces200Response.from_dict(list_traces200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


