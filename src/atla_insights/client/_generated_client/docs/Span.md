# Span


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
**annotations** | [**List[Annotation]**](Annotation.md) |  | [optional] 

## Example

```python
from _generated_client.models.span import Span

# TODO update the JSON string below
json = "{}"
# create an instance of Span from a JSON string
span_instance = Span.from_json(json)
# print the JSON string representation of the object
print(Span.to_json())

# convert the object into a dict
span_dict = span_instance.to_dict()
# create an instance of Span from a dict
span_from_dict = Span.from_dict(span_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


