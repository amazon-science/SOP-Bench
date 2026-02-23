#!/bin/bash

# Script to remove trace files containing AWS exceptions
# Usage: ./cleanup_traces.sh [directory_pattern]
# Example: ./cleanup_traces.sh results/*_traces
# Default: results/*_traces

TRACE_DIR_PATTERN="${1:-results/*_traces}"

echo "Cleaning up trace files with AWS exceptions..."

# Find and remove files with ExpiredTokenException
expired_files=$(find $TRACE_DIR_PATTERN -name "*.txt" -exec grep -l "ExpiredTokenException" {} \; 2>/dev/null)
if [ -n "$expired_files" ]; then
    echo "$expired_files" | xargs rm -f
    echo "Removed $(echo "$expired_files" | wc -l) files with ExpiredTokenException"
else
    echo "No files with ExpiredTokenException found"
fi

# Find and remove files with serviceUnavailableException
unavailable_files=$(find $TRACE_DIR_PATTERN -name "*.txt" -exec grep -l "ServiceUnavailableException" {} \; 2>/dev/null)
if [ -n "$unavailable_files" ]; then
    echo "$unavailable_files" | xargs rm -f
    echo "Removed $(echo "$unavailable_files" | wc -l) files with ServiceUnavailableException"
else
    echo "No files with ServiceUnavailableException found"
fi

# Find and remove files with ValidationException
validation_files=$(find $TRACE_DIR_PATTERN -name "*.txt" -exec grep -l "ValidationException" {} \; 2>/dev/null)
if [ -n "$validation_files" ]; then
    echo "$validation_files" | xargs rm -f
    echo "Removed $(echo "$validation_files" | wc -l) files with ValidationException"
else
    echo "No files with ValidationException found"
fi

# Find and remove files with EndpointConnectionError
endpoint_files=$(find $TRACE_DIR_PATTERN -name "*.txt" -exec grep -l "EndpointConnectionError" {} \; 2>/dev/null)
if [ -n "$endpoint_files" ]; then
    echo "$endpoint_files" | xargs rm -f
    echo "Removed $(echo "$endpoint_files" | wc -l) files with EndpointConnectionError"
else
    echo "No files with EndpointConnectionError found"
fi

# Find and remove files with ThrottlingException
throttling_files=$(find $TRACE_DIR_PATTERN -name "*.txt" -exec grep -l "ThrottlingException" {} \; 2>/dev/null)
if [ -n "$throttling_files" ]; then
    echo "$throttling_files" | xargs rm -f
    echo "Removed $(echo "$throttling_files" | wc -l) files with ThrottlingException"
else
    echo "No files with ThrottlingException found"
fi

echo "Cleanup complete!"
