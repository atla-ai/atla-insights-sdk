# TraceWithDetails


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
**spans** | [**List[Span]**](Span.md) |  | [optional] 
**custom_metric_values** | [**List[CustomMetricValue]**](CustomMetricValue.md) |  | [optional] 

## Example

```python
from _generated_client.models.trace_with_details import TraceWithDetails

# TODO update the JSON string below
json = "{}"
# create an instance of TraceWithDetails from a JSON string
trace_with_details_instance = TraceWithDetails.from_json(json)
# print the JSON string representation of the object
print(TraceWithDetails.to_json())

# convert the object into a dict
trace_with_details_dict = trace_with_details_instance.to_dict()
# create an instance of TraceWithDetails from a dict
trace_with_details_from_dict = TraceWithDetails.from_dict(trace_with_details_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


