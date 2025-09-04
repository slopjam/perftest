# External Chrome Performance Testing Tool

A Python tool for measuring Core Web Vitals and performance metrics by connecting to an external Chrome browser via CDP (Chrome DevTools Protocol). This approach bypasses bot detection on sites that block automated testing.

## Features

- **Detailed LCP/FCP Explanations**: Shows exactly how metrics were determined, which elements were measured, and measurement timelines
- **Cold/Warm Cache Testing**: Clear cache and reload for cold measurements, or test with existing cache
- **Bot Detection Bypass**: Uses real Chrome browser instead of headless automation
- **Comprehensive Metrics**: Core Web Vitals (LCP, FCP, CLS), Navigation Timing, Resource Analysis
- **Flexible Configuration**: YAML/JSON config files and CLI arguments
- **Multi-run Statistics**: Run multiple tests and get statistical analysis

## Quick Start

### 1. Start Chrome with Remote Debugging

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-debug
```

**Linux/Mac:**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

### 2. Install Dependencies

```bash
pip install playwright pyyaml
```

### 3. Run Performance Test

```bash
# Single cold cache test with detailed explanations
python external_perf_tool_detailed.py "https://www.costco.com" --cache cold

# Multi-run test with statistics
python external_perf_tool_detailed.py "https://www.bestbuy.com" --cache warm --runs 3

# Use config file
python external_perf_tool_detailed.py "https://site.com" --config perf_config.yaml

# Add custom HTTP headers
python external_perf_tool_detailed.py "https://site.com" --headers "User-Agent: Custom Agent" --headers "Authorization: Bearer token123"
```

## Example Output

```
🎯 Starting cold cache performance test with detailed metrics...
================================================================================
🧪 Run 1/1 - cold cache test...
   📍 Navigating to https://www.costco.com
   🧹 Clearing cache and cookies for cold measurement...
   🔄 Reloading page for cold cache measurement...
   ✅ Run 1: FCP=440ms, LCP=3076ms, TTFB=192.2ms, Resources=220

📋 DETAILED METRICS EXPLANATION - Run 1:
------------------------------------------------------------
🎨 First Contentful Paint (FCP):
   ✅ Value: 440.0ms
   📊 Source: performance.getEntriesByType("paint")
   🔍 Method: Found 'first-contentful-paint' entry in paint timing

🖼️  Largest Contentful Paint (LCP):
   ✅ Value: 3076.0ms
   📊 Source: PerformanceObserver with buffered entries
   📈 LCP Timeline (2 measurements):
      1. 440.0ms (size: 92951px²) - ⏭️  superseded
      2. 3076.0ms (size: 158200px²) - 🏁 FINAL
   🎯 LCP Element:
      Tag: <img>
      Class: .MuiBox-root mui-n4nkj5
      Source: https://bfasset.costco-static.com/56O3HXZ9/at/c4g86pnj7rrbhckwsprc344p/d_25w1231...

📊 FINAL PERFORMANCE ANALYSIS (cold cache):
✅ Successful tests: 1/1
FCP: avg=440.0ms, range=440.0-440.0ms
LCP: avg=3076.0ms, range=3076.0-3076.0ms
TTFB: avg=192.2ms, range=192.2-192.2ms

🎯 Overall Rating: GOOD
   FCP: excellent
   LCP: good
```

## Configuration

Create `perf_config.yaml`:

```yaml
# Chrome DevTools Protocol URL
cdp_url: http://localhost:9222

# Time to wait for page stabilization after load (seconds)
stabilization_time: 3

# Performance thresholds (milliseconds)
thresholds:
  fcp:
    excellent: 1800  # < 1.8s
    good: 3000      # < 3s
  lcp:
    excellent: 2500  # < 2.5s  
    good: 4000      # < 4s

# Advanced settings
advanced:
  lcp_wait_time: 3
  max_slow_resources: 5
```

## CLI Options

```
usage: external_perf_tool_detailed.py [-h] [--cache {warm,cold}] [--runs RUNS]
                                      [--config CONFIG] [--output OUTPUT]
                                      [--cdp-url CDP_URL] [--wait WAIT]
                                      [--headers HEADERS]
                                      url

positional arguments:
  url                  URL to test

options:
  --cache {warm,cold}  Cache mode (default: warm)
  --runs RUNS          Number of test runs (default: 1)
  --config CONFIG      Path to config file (JSON or YAML)
  --output OUTPUT      Output file path (auto-generated if not specified)
  --cdp-url CDP_URL    Chrome DevTools Protocol URL (default: http://localhost:9222)
  --wait WAIT          Wait time between runs in seconds (default: 5)
  --headers HEADERS    Add HTTP header (format: "Header: Value"). Can be used multiple times.
```

## How It Works

1. **External Chrome Connection**: Connects to Chrome via CDP instead of launching headless browser
2. **Cache Control**: For cold cache tests, loads page → clears cache → reloads for known state
3. **LCP Tracking**: Uses PerformanceObserver with buffered entries to capture all LCP changes
4. **Detailed Analysis**: Tracks which elements become LCP and shows timeline of changes
5. **Bot Detection Bypass**: Since it uses real Chrome with real user session, passes all bot detection

## Core Web Vitals Measured

- **LCP (Largest Contentful Paint)**: Time when largest content element renders
- **FCP (First Contentful Paint)**: Time when first content appears
- **CLS (Cumulative Layout Shift)**: Visual stability score
- **TTFB (Time to First Byte)**: Server response time

## Why External Chrome?

Many sites block automated browsers but allow real Chrome connections. This tool:
- ✅ Works on sites that block Playwright/Selenium
- ✅ Provides accurate real-world performance data
- ✅ Bypasses sophisticated bot detection
- ✅ Uses actual user's network conditions and location

## Troubleshooting

**Chrome not connecting**: Make sure Chrome is running with `--remote-debugging-port=9222`

**NetworkIdle timeout**: Tool automatically falls back to `domcontentloaded` wait condition

**No LCP data**: Some sites need longer stabilization time - increase in config file

**Permission denied**: Ensure Chrome debug port (9222) is not blocked by firewall