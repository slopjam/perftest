#!/usr/bin/env python3
"""Enhanced performance testing tool with detailed LCP/FCP reporting."""

import asyncio
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright

class DetailedExternalPerfTool:
    """Performance testing tool with explicit LCP/FCP determination details."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cdp_url = config.get('cdp_url', 'http://localhost:9222')
        
    async def run_test(
        self, 
        url: str, 
        cache_mode: str = 'warm',
        runs: int = 1,
        wait_time: int = 5
    ) -> Dict[str, Any]:
        """Run performance test with detailed reporting."""
        
        print(f"🎯 Starting {cache_mode} cache performance test with detailed metrics...")
        print(f"   URL: {url}")
        print(f"   Runs: {runs}")
        print(f"   Cache mode: {cache_mode}")
        print("=" * 80)
        
        all_results = []
        
        for run in range(1, runs + 1):
            result = await self._run_single_test(url, cache_mode, run, runs)
            if result:
                all_results.append(result)
                # Print detailed metrics explanation for each run
                self._print_detailed_explanation(result, run)
            
            if run < runs:
                print(f"   ⏳ Waiting {wait_time}s before next run...")
                await asyncio.sleep(wait_time)
        
        # Analyze results
        analysis = self._analyze_results(all_results, cache_mode)
        
        return {
            'test_config': {
                'url': url,
                'cache_mode': cache_mode,
                'runs': runs,
                'timestamp': datetime.now().isoformat()
            },
            'results': all_results,
            'analysis': analysis
        }
    
    def _print_detailed_explanation(self, result: Dict[str, Any], run: int):
        """Print detailed explanation of how metrics were determined."""
        
        print(f"\n📋 DETAILED METRICS EXPLANATION - Run {run}:")
        print("-" * 60)
        
        web_vitals = result.get('web_vitals', {})
        
        # FCP Explanation
        fcp_details = web_vitals.get('fcp_details', {})
        print("🎨 First Contentful Paint (FCP):")
        if web_vitals.get('fcp'):
            print(f"   ✅ Value: {web_vitals['fcp']:.1f}ms")
            default_source = 'performance.getEntriesByType("paint")'
            print(f"   📊 Source: {fcp_details.get('source', default_source)}")
            print(f"   🔍 Method: Found 'first-contentful-paint' entry in paint timing")
            if fcp_details.get('all_paint_entries'):
                print(f"   📝 Paint entries found: {len(fcp_details['all_paint_entries'])}")
                for entry in fcp_details['all_paint_entries']:
                    print(f"      - {entry['name']}: {entry['startTime']:.1f}ms")
        else:
            print("   ❌ Not measured - no FCP entries found")
        
        # LCP Explanation  
        lcp_details = web_vitals.get('lcp_details', {})
        print("\n🖼️  Largest Contentful Paint (LCP):")
        if web_vitals.get('lcp'):
            print(f"   ✅ Value: {web_vitals['lcp']:.1f}ms")
            print(f"   📊 Source: PerformanceObserver with buffered entries")
            print(f"   🔍 Method: Monitored LCP changes over 3 seconds")
            
            if lcp_details.get('measurements'):
                print(f"   📈 LCP Timeline ({len(lcp_details['measurements'])} measurements):")
                for measurement in lcp_details['measurements']:
                    status = "🏁 FINAL" if measurement['reason'] == 'final_lcp' else "⏭️  superseded"
                    print(f"      {measurement['sequence']}. {measurement['timing']:.1f}ms (size: {measurement['size']}px²) - {status}")
            
            final_element = lcp_details.get('finalElement')
            if final_element:
                print(f"   🎯 LCP Element:")
                print(f"      Tag: <{final_element.get('tagName', 'unknown').lower()}>")
                if final_element.get('id'):
                    print(f"      ID: #{final_element['id']}")
                if final_element.get('className'):
                    print(f"      Class: .{final_element['className']}")
                if final_element.get('src'):
                    print(f"      Source: {final_element['src']}")
                if final_element.get('textContent'):
                    print(f"      Text: '{final_element['textContent']}'")
            
            if lcp_details.get('entries'):
                print(f"   🔄 Total LCP candidates evaluated: {len(lcp_details['entries'])}")
        else:
            print("   ❌ Not measured")
            print(f"   🔍 Reason: {lcp_details.get('reason', 'No LCP entries captured')}")
        
        # Navigation Timing Explanation
        nav_timing = result.get('navigation', {})
        print(f"\n⏱️  Navigation Timing:")
        print(f"   🌐 DNS Lookup: {nav_timing.get('dns_lookup', 'N/A')}ms")
        print(f"   🤝 TCP Connect: {nav_timing.get('tcp_connect', 'N/A')}ms")  
        print(f"   🔒 SSL Handshake: {nav_timing.get('ssl_handshake', 'N/A')}ms")
        print(f"   📡 TTFB: {nav_timing.get('ttfb', 'N/A'):.1f}ms (responseStart - requestStart)")
        print(f"   📄 DOM Content Loaded: {nav_timing.get('dom_content_loaded', 'N/A')}ms")
        
        # Resources Summary
        resources = result.get('resources', {})
        print(f"\n📦 Resources Analysis:")
        print(f"   📊 Total loaded: {resources.get('total_count', 'N/A')}")
        print(f"   💾 Total size: {resources.get('total_size', 0) / 1024:.1f} KB")
        
        if resources.get('slowest'):
            print(f"   🐌 Top 3 slowest resources:")
            for i, res in enumerate(resources['slowest'][:3], 1):
                size_info = f" ({res['size'] / 1024:.1f}KB)" if res['size'] > 0 else ""
                print(f"      {i}. {res['type']}: {res['duration']:.1f}ms{size_info}")
                print(f"         {res['name'][:70]}...")
    
    async def _run_single_test(self, url: str, cache_mode: str, run: int, total: int) -> Optional[Dict[str, Any]]:
        """Run a single performance test with detailed metrics."""
        
        print(f"🧪 Run {run}/{total} - {cache_mode} cache test...")
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(self.cdp_url)
                context = browser.contexts[0]
                page = context.pages[0]
                
                # Set custom HTTP headers if provided
                headers = self.config.get('headers', {})
                if headers:
                    print(f"   🔧 Setting custom HTTP headers: {list(headers.keys())}")
                    await page.set_extra_http_headers(headers)
                
                # Always navigate to ensure we're on the right page
                print(f"   📍 Navigating to {url}")
                try:
                    await page.goto(url, wait_until="networkidle", timeout=15000)
                except Exception:
                    print("   ⚠️  NetworkIdle timeout, trying domcontentloaded...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                # Handle cache - for cold cache, clear then reload for known state
                if cache_mode == 'cold':
                    print("   🧹 Clearing cache and cookies for cold measurement...")
                    client = await context.new_cdp_session(page)
                    await client.send('Network.clearBrowserCache')
                    await client.send('Network.clearBrowserCookies')
                    print("   🔄 Reloading page for cold cache measurement...")
                    try:
                        await page.reload(wait_until="networkidle", timeout=15000)
                    except Exception:
                        print("   ⚠️  NetworkIdle timeout on reload, using domcontentloaded...")
                        await page.reload(wait_until="domcontentloaded", timeout=15000)
                elif cache_mode == 'warm':
                    print("   ♨️  Using warm cache (page already loaded)")
                    await asyncio.sleep(1)
                
                # Stabilization
                stabilization_time = self.config.get('stabilization_time', 3)
                await asyncio.sleep(stabilization_time)
                
                # Collect detailed metrics
                metrics = await self._collect_detailed_metrics(page)
                
                # Quick summary
                fcp = metrics.get('web_vitals', {}).get('fcp', 'N/A')
                lcp = metrics.get('web_vitals', {}).get('lcp', 'N/A')
                ttfb = metrics.get('navigation', {}).get('ttfb', 'N/A')
                resources = metrics.get('resources', {}).get('total_count', 'N/A')
                
                print(f"   ✅ Run {run}: FCP={fcp}ms, LCP={lcp}ms, TTFB={ttfb:.1f}ms, Resources={resources}")
                
                metrics['run_number'] = run
                metrics['cache_mode'] = cache_mode
                return metrics
                
            except Exception as e:
                print(f"   ❌ Run {run} failed: {e}")
                return None
            finally:
                await browser.close()
    
    async def _collect_detailed_metrics(self, page) -> Dict[str, Any]:
        """Collect comprehensive performance metrics with detailed explanations."""
        
        metrics = await page.evaluate("""
            async () => {
                const results = { timestamp: Date.now() };
                
                // Navigation timing (unchanged)
                const navigation = performance.getEntriesByType('navigation')[0];
                if (navigation) {
                    results.navigation = {
                        dns_lookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                        tcp_connect: navigation.connectEnd - navigation.connectStart,
                        ssl_handshake: navigation.secureConnectionStart > 0 ? 
                            navigation.connectEnd - navigation.secureConnectionStart : null,
                        ttfb: navigation.responseStart - navigation.requestStart,
                        dom_content_loaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        load_complete: navigation.loadEventEnd - navigation.loadEventStart
                    };
                }
                
                const vitals = {};
                
                // Detailed FCP collection
                const paintEntries = performance.getEntriesByType('paint');
                const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
                if (fcpEntry) {
                    vitals.fcp = fcpEntry.startTime;
                    vitals.fcp_details = {
                        source: 'performance.getEntriesByType("paint")',
                        method: 'Standard Paint Timing API',
                        all_paint_entries: paintEntries.map(entry => ({
                            name: entry.name,
                            startTime: entry.startTime
                        }))
                    };
                } else {
                    vitals.fcp_details = {
                        reason: 'No first-contentful-paint entry found',
                        all_paint_entries: paintEntries.map(entry => ({
                            name: entry.name,
                            startTime: entry.startTime
                        }))
                    };
                }
                
                // CLS (unchanged)
                let cls = 0;
                const clsEntries = performance.getEntriesByType('layout-shift');
                for (const entry of clsEntries) {
                    if (!entry.hadRecentInput) {
                        cls += entry.value;
                    }
                }
                vitals.cls = cls;
                
                // Resources (enhanced)
                const resources = performance.getEntriesByType('resource');
                results.resources = {
                    total_count: resources.length,
                    total_size: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
                    collection_method: 'performance.getEntriesByType("resource")',
                    slowest: resources
                        .sort((a, b) => b.duration - a.duration)
                        .slice(0, 5)
                        .map(r => ({
                            name: r.name,
                            type: r.initiatorType,
                            duration: r.duration,
                            size: r.transferSize || 0
                        }))
                };
                
                // Detailed LCP collection with full tracking
                const lcpPromise = new Promise((resolve) => {
                    const lcpDetails = {
                        value: null,
                        entries: [],
                        finalElement: null,
                        measurements: [],
                        method: 'PerformanceObserver with buffered entries'
                    };
                    
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        for (const entry of entries) {
                            lcpDetails.value = entry.startTime;
                            
                            // Detailed entry information
                            const entryDetail = {
                                startTime: entry.startTime,
                                size: entry.size || 0,
                                loadTime: entry.loadTime || 0,
                                renderTime: entry.renderTime || 0,
                                element: entry.element ? {
                                    tagName: entry.element.tagName,
                                    id: entry.element.id || '',
                                    className: entry.element.className || '',
                                    src: entry.element.src ? entry.element.src.substring(0, 80) + '...' : '',
                                    textContent: entry.element.textContent ? 
                                        entry.element.textContent.substring(0, 80).replace(/\\s+/g, ' ').trim() + '...' : ''
                                } : null
                            };
                            
                            lcpDetails.entries.push(entryDetail);
                        }
                    });
                    
                    observer.observe({type: 'largest-contentful-paint', buffered: true});
                    
                    setTimeout(() => {
                        observer.disconnect();
                        
                        // Process measurements for timeline
                        if (lcpDetails.entries.length > 0) {
                            lcpDetails.finalElement = lcpDetails.entries[lcpDetails.entries.length - 1].element;
                            lcpDetails.measurements = lcpDetails.entries.map((entry, i) => ({
                                sequence: i + 1,
                                timing: entry.startTime,
                                size: entry.size,
                                reason: i === lcpDetails.entries.length - 1 ? 'final_lcp' : 'superseded'
                            }));
                        } else {
                            lcpDetails.reason = 'No LCP entries captured by observer';
                        }
                        
                        resolve(lcpDetails);
                    }, 3000);
                });
                
                const lcpResult = await lcpPromise;
                vitals.lcp = lcpResult.value;
                vitals.lcp_details = lcpResult;
                
                results.web_vitals = vitals;
                return results;
            }
        """)
        
        return metrics
    
    def _analyze_results(self, results: list, cache_mode: str) -> Dict[str, Any]:
        """Analyze results (same as original)."""
        
        if not results:
            return {'error': 'No successful tests to analyze'}
        
        # Extract metrics
        fcps = [r['web_vitals']['fcp'] for r in results if r.get('web_vitals', {}).get('fcp')]
        lcps = [r['web_vitals']['lcp'] for r in results if r.get('web_vitals', {}).get('lcp')]
        ttfbs = [r['navigation']['ttfb'] for r in results if r.get('navigation', {}).get('ttfb')]
        resource_counts = [r['resources']['total_count'] for r in results if r.get('resources', {}).get('total_count')]
        
        def stats(values, name):
            if not values:
                return {name: 'No data'}
            return {
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'median': sorted(values)[len(values) // 2]
            }
        
        analysis = {
            'successful_tests': len(results),
            'cache_mode': cache_mode,
            'metrics': {
                'fcp': stats(fcps, 'fcp'),
                'lcp': stats(lcps, 'lcp'), 
                'ttfb': stats(ttfbs, 'ttfb'),
                'resources': stats(resource_counts, 'resources')
            }
        }
        
        # Performance assessment
        fcp_avg = analysis['metrics']['fcp'].get('avg', float('inf'))
        lcp_avg = analysis['metrics']['lcp'].get('avg', float('inf'))
        
        analysis['assessment'] = {
            'fcp_rating': 'excellent' if fcp_avg < 1800 else 'good' if fcp_avg < 3000 else 'poor',
            'lcp_rating': 'excellent' if lcp_avg < 2500 else 'good' if lcp_avg < 4000 else 'poor',
            'overall_rating': 'excellent' if fcp_avg < 1800 and lcp_avg < 2500 else 'good' if fcp_avg < 3000 and lcp_avg < 4000 else 'needs_improvement'
        }
        
        return analysis

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    
    default_config = {
        'cdp_url': 'http://localhost:9222',
        'stabilization_time': 3,
        'output_format': 'json',
        'output_dir': './results'
    }
    
    if not config_path:
        return default_config
    
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"⚠️  Config file {config_path} not found, using defaults")
        return default_config
    
    try:
        with open(config_file) as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                file_config = yaml.safe_load(f)
            else:
                file_config = json.load(f)
        
        merged_config = default_config.copy()
        merged_config.update(file_config)
        return merged_config
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return default_config

def main():
    parser = argparse.ArgumentParser(description='External Chrome Performance Testing Tool with Detailed Explanations')
    parser.add_argument('url', help='URL to test')
    parser.add_argument('--cache', choices=['warm', 'cold'], default='warm', 
                       help='Cache mode (default: warm)')
    parser.add_argument('--runs', type=int, default=1, 
                       help='Number of test runs (default: 1)')
    parser.add_argument('--config', type=str, 
                       help='Path to config file (JSON or YAML)')
    parser.add_argument('--output', type=str, 
                       help='Output file path (auto-generated if not specified)')
    parser.add_argument('--cdp-url', type=str, default='http://localhost:9222',
                       help='Chrome DevTools Protocol URL (default: http://localhost:9222)')
    parser.add_argument('--wait', type=int, default=5,
                       help='Wait time between runs in seconds (default: 5)')
    parser.add_argument('--headers', type=str, action='append',
                       help='Add HTTP header (format: "Header: Value"). Can be used multiple times.')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    if args.cdp_url != 'http://localhost:9222':
        config['cdp_url'] = args.cdp_url
    
    # Process headers from CLI
    if args.headers:
        headers = {}
        for header_str in args.headers:
            if ':' in header_str:
                key, value = header_str.split(':', 1)
                headers[key.strip()] = value.strip()
            else:
                print(f"⚠️  Invalid header format: {header_str} (expected 'Header: Value')")
        if headers:
            config['headers'] = headers
    
    tool = DetailedExternalPerfTool(config)
    
    async def run_test():
        try:
            results = await tool.run_test(
                url=args.url,
                cache_mode=args.cache,
                runs=args.runs,
                wait_time=args.wait
            )
            
            # Display final analysis
            analysis = results['analysis']
            print(f"\n📊 FINAL PERFORMANCE ANALYSIS ({args.cache} cache):")
            print("=" * 80)
            print(f"✅ Successful tests: {analysis['successful_tests']}/{args.runs}")
            
            metrics = analysis['metrics']
            for metric_name, stats in metrics.items():
                if isinstance(stats, dict) and 'avg' in stats:
                    unit = 'ms' if metric_name != 'resources' else ' items'
                    print(f"{metric_name.upper()}: avg={stats['avg']:.1f}{unit}, range={stats['min']:.1f}-{stats['max']:.1f}{unit}")
            
            assessment = analysis['assessment']
            print(f"\n🎯 Overall Rating: {assessment['overall_rating'].upper()}")
            print(f"   FCP: {assessment['fcp_rating']}")
            print(f"   LCP: {assessment['lcp_rating']}")
            
            # Save results
            if args.output:
                output_path = args.output
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_url = args.url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_')
                output_path = f"detailed_perf_{safe_url}_{args.cache}_{timestamp}.json"
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Detailed results saved to: {output_path}")
            
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    main()