# ListTraces200ResponseTracesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**environment** | **str** |  | 
**is_success** | **bool** |  | 
**is_completed** | **bool** |  | 
**metadata** | **Dict[str, object]** |  | 
**started_at** | **str** |  | 
**ended_at** | **str** |  | 

## Example

```python
from _generated_client.models.list_traces200_response_traces_inner import ListTraces200ResponseTracesInner

# TODO update the JSON string below
json = "{}"
# create an instance of ListTraces200ResponseTracesInner from a JSON string
list_traces200_response_traces_inner_instance = ListTraces200ResponseTracesInner.from_json(json)
# print the JSON string representation of the object
print(ListTraces200ResponseTracesInner.to_json())

# convert the object into a dict
list_traces200_response_traces_inner_dict = list_traces200_response_traces_inner_instance.to_dict()
# create an instance of ListTraces200ResponseTracesInner from a dict
list_traces200_response_traces_inner_from_dict = ListTraces200ResponseTracesInner.from_dict(list_traces200_response_traces_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


