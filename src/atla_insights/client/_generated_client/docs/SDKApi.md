# _generated_client.SDKApi

All URIs are relative to *https://app.atla-ai.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_trace_by_id**](SDKApi.md#get_trace_by_id) | **GET** /api/sdk/v1/traces/{traceId} | Get a single trace by ID
[**get_traces_by_ids**](SDKApi.md#get_traces_by_ids) | **GET** /api/sdk/v1/traces/ids | Get multiple traces by IDs
[**list_traces**](SDKApi.md#list_traces) | **GET** /api/sdk/v1/traces | List traces with pagination and filtering


# **get_trace_by_id**
> TraceDetailResponse get_trace_by_id(trace_id, include=include)

Get a single trace by ID

Retrieve a specific trace by its unique identifier. Returns complete trace data including all spans, annotations, trace summary, and custom metric values.

### Example


```python
import _generated_client
from _generated_client.models.trace_detail_response import TraceDetailResponse
from _generated_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://app.atla-ai.com
# See configuration.py for a list of all supported configuration parameters.
configuration = _generated_client.Configuration(
    host = "https://app.atla-ai.com"
)


# Enter a context with an instance of the API client
with _generated_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = _generated_client.SDKApi(api_client)
    trace_id = 'trace_id_example' # str | 
    include = ['include_example'] # List[str] |  (optional)

    try:
        # Get a single trace by ID
        api_response = api_instance.get_trace_by_id(trace_id, include=include)
        print("The response of SDKApi->get_trace_by_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SDKApi->get_trace_by_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **trace_id** | **str**|  | 
 **include** | [**List[str]**](str.md)|  | [optional] 

### Return type

[**TraceDetailResponse**](TraceDetailResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successfully retrieved trace with complete data |  -  |
**401** | Unauthorized - Invalid or missing API key |  -  |
**404** | Trace not found or access denied |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_traces_by_ids**
> DetailedTraceListResponse get_traces_by_ids(ids, include=include)

Get multiple traces by IDs

Retrieve specific traces by providing an array of trace IDs. Returns complete trace data including spans, summaries, and custom metrics for all found traces.

### Example


```python
import _generated_client
from _generated_client.models.detailed_trace_list_response import DetailedTraceListResponse
from _generated_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://app.atla-ai.com
# See configuration.py for a list of all supported configuration parameters.
configuration = _generated_client.Configuration(
    host = "https://app.atla-ai.com"
)


# Enter a context with an instance of the API client
with _generated_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = _generated_client.SDKApi(api_client)
    ids = ['ids_example'] # List[str] | 
    include = ['include_example'] # List[str] |  (optional)

    try:
        # Get multiple traces by IDs
        api_response = api_instance.get_traces_by_ids(ids, include=include)
        print("The response of SDKApi->get_traces_by_ids:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SDKApi->get_traces_by_ids: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ids** | [**List[str]**](str.md)|  | 
 **include** | [**List[str]**](str.md)|  | [optional] 

### Return type

[**DetailedTraceListResponse**](DetailedTraceListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successfully retrieved traces matching the provided IDs |  -  |
**401** | Unauthorized - Invalid or missing API key |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_traces**
> TraceListResponse list_traces(start_timestamp=start_timestamp, end_timestamp=end_timestamp, metadata_filter=metadata_filter, page=page, page_size=page_size)

List traces with pagination and filtering

Retrieve a paginated list of traces for the authenticated organization.

### Example


```python
import _generated_client
from _generated_client.models.trace_list_response import TraceListResponse
from _generated_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://app.atla-ai.com
# See configuration.py for a list of all supported configuration parameters.
configuration = _generated_client.Configuration(
    host = "https://app.atla-ai.com"
)


# Enter a context with an instance of the API client
with _generated_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = _generated_client.SDKApi(api_client)
    start_timestamp = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    end_timestamp = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
    metadata_filter = 'metadata_filter_example' # str | URL-encoded JSON array of metadata key-value pairs: [{\"key\":\"version\",\"value\":\"1\"}] (optional)
    page = 1 # int |  (optional) (default to 1)
    page_size = 50 # int |  (optional) (default to 50)

    try:
        # List traces with pagination and filtering
        api_response = api_instance.list_traces(start_timestamp=start_timestamp, end_timestamp=end_timestamp, metadata_filter=metadata_filter, page=page, page_size=page_size)
        print("The response of SDKApi->list_traces:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SDKApi->list_traces: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **start_timestamp** | **datetime**|  | [optional] 
 **end_timestamp** | **datetime**|  | [optional] 
 **metadata_filter** | **str**| URL-encoded JSON array of metadata key-value pairs: [{\&quot;key\&quot;:\&quot;version\&quot;,\&quot;value\&quot;:\&quot;1\&quot;}] | [optional] 
 **page** | **int**|  | [optional] [default to 1]
 **page_size** | **int**|  | [optional] [default to 50]

### Return type

[**TraceListResponse**](TraceListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successfully retrieved paginated list of traces |  -  |
**401** | Unauthorized - Invalid or missing API key |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

