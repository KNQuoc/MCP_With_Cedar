#!/usr/bin/env python3
"""
Test script for SpellsSpecialistTool
Tests all actions and various query/focus combinations
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock

# Add the cedar_mcp directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from cedar_mcp.tools.spells_specialist import SpellsSpecialistTool
from cedar_mcp.services.docs import DocsIndex


class MockDocsIndex:
    """Mock DocsIndex for testing without actual documentation files"""
    
    async def search(self, query: str, limit: int = 5, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """Return mock search results based on query"""
        
        # Create mock results based on query keywords
        mock_results = []
        
        if "radial" in query.lower() or "menu" in query.lower():
            mock_results.append({
                "source": "cedar-docs",
                "heading": "RadialMenu Component",
                "content": """
```tsx
import { useSpell, ActivationMode, Hotkey } from 'cedar-os';
import { RadialMenu } from 'cedar-os-components/spells';

function MyRadialMenu() {
  const { isActive } = useSpell({
    id: 'main-menu',
    activationConditions: {
      events: [Hotkey.SPACE],
      mode: ActivationMode.HOLD
    }
  });
  
  return isActive ? (
    <RadialMenu
      items={[
        { icon: '🏠', label: 'Home', action: () => navigate('/') },
        { icon: '⚙️', label: 'Settings', action: () => openSettings() }
      ]}
    />
  ) : null;
}
```
The RadialMenu creates circular menus activated by gestures. Components auto-position to stay on screen.""",
                "url": "https://docs.cedarcopilot.com/spells/radial-menu"
            })
        
        if "useSpell" in query or "custom" in query.lower():
            mock_results.append({
                "source": "cedar-docs",
                "heading": "Creating Custom Spells",
                "content": """
Create custom spells with the useSpell hook:

```typescript
const { isActive, deactivate } = useSpell({
  id: 'command-palette',
  activationConditions: {
    events: ['cmd+k', 'ctrl+k'],
    mode: ActivationMode.TOGGLE
  },
  onActivate: (state) => {
    console.log('Activated with:', state.triggerData);
  },
  preventDefaultEvents: true
});
```

The useSpell hook provides isActive state and control methods.""",
                "url": "https://docs.cedarcopilot.com/spells/creating-custom-spells"
            })
        
        if "questioning" in query.lower():
            mock_results.append({
                "source": "cedar-docs", 
                "heading": "QuestioningSpell",
                "content": """
QuestioningSpell provides interactive tooltips:

```tsx
import { QuestioningSpell } from 'cedar-os-components/spells';

function App() {
  return (
    <>
      <QuestioningSpell />
      <button data-question="This button saves your work">Save</button>
    </>
  );
}
```

Add data-question attributes to elements for tooltips.""",
                "url": "https://docs.cedarcopilot.com/spells/questioning-spell"
            })
        
        if "activation" in query.lower() or "trigger" in query.lower():
            mock_results.append({
                "source": "cedar-docs",
                "heading": "Activation Conditions",
                "content": """
Spells support multiple activation methods:
- Keyboard: Hotkey.SPACE, 'cmd+k', 'ctrl+shift+p'
- Mouse: MouseEvent.RIGHT_CLICK, DOUBLE_CLICK
- Selection: SelectionEvent.TEXT_SELECT

Activation modes control lifecycle:
- ActivationMode.TOGGLE - Press to activate/deactivate
- ActivationMode.HOLD - Active while held
- ActivationMode.TRIGGER - Fire once with cooldown""",
                "url": "https://docs.cedarcopilot.com/spells/activation"
            })
        
        if "error" in query.lower() or "not working" in query.lower():
            mock_results.append({
                "source": "cedar-docs",
                "heading": "Troubleshooting Spells",
                "content": """
Common issues and solutions:
1. Spell not activating: Check for duplicate spell IDs
2. Keyboard shortcuts not working: Add preventDefaultEvents: true
3. Activation in inputs: Set ignoreInputElements: true
4. Check browser console for specific error messages""",
                "url": "https://docs.cedarcopilot.com/spells/troubleshooting"
            })
        
        # If no specific matches, add general spell documentation
        if not mock_results:
            mock_results.append({
                "source": "cedar-docs",
                "heading": "Spells Overview",
                "content": """Cedar spells enable gesture-based interactions, radial menus, and keyboard shortcuts. 
Built on the useSpell hook with pre-built components like RadialMenu and QuestioningSpell.""",
                "url": "https://docs.cedarcopilot.com/spells/overview"
            })
        
        return mock_results[:limit]


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(result: Dict[str, Any], verbose: bool = False):
    """Pretty print the result"""
    if verbose:
        # Full JSON output
        print(json.dumps(result, indent=2))
    else:
        # Summarized output
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Print main info
        if "action" in result:
            print(f"📋 Action: {result['action']}")
        if "query" in result:
            print(f"🔍 Query: {result['query']}")
        if "focus" in result:
            print(f"🎯 Focus: {result['focus']}")
        
        # Print guidance if available
        if "guidance" in result:
            print(f"\n💡 Guidance:")
            print(f"   {result['guidance']}")
        
        # Print results count
        if "results" in result:
            print(f"\n📚 Documentation Results: {len(result['results'])} found")
            for i, doc in enumerate(result['results'][:3], 1):
                heading = doc.get('heading', 'Unknown')
                print(f"   {i}. {heading}")
        
        # Print code examples
        if "code_examples" in result:
            print(f"\n💻 Code Examples: {len(result['code_examples'])} found")
            for i, example in enumerate(result['code_examples'][:2], 1):
                lang = example.get('language', 'unknown')
                source = example.get('source', 'Unknown')
                print(f"   {i}. {lang} from {source}")
        
        # Print implementation steps
        if "implementation_steps" in result:
            print(f"\n📝 Implementation Steps:")
            for i, step in enumerate(result['implementation_steps'][:5], 1):
                print(f"   {i}. {step}")
        
        # Print common solutions
        if "common_solutions" in result:
            print(f"\n✅ Common Solutions:")
            for i, solution in enumerate(result['common_solutions'], 1):
                print(f"   {i}. {solution}")
        
        # Print diagnostic steps
        if "diagnostic_steps" in result:
            print(f"\n🔧 Diagnostic Steps:")
            for i, step in enumerate(result['diagnostic_steps'][:5], 1):
                print(f"   {i}. {step}")
        
        # Print available features
        if "available_features" in result:
            print(f"\n🎨 Available Features: {len(result['available_features'])} features")
            for i, feature in enumerate(result['available_features'][:5], 1):
                print(f"   {i}. {feature}")
        
        # Print use cases
        if "use_cases" in result:
            print(f"\n💼 Use Cases:")
            for i, use_case in enumerate(result['use_cases'][:3], 1):
                print(f"   {i}. {use_case}")
        
        # Print related topics
        if "related_topics" in result:
            print(f"\n🔗 Related Topics:")
            for i, topic in enumerate(result['related_topics'], 1):
                print(f"   {i}. {topic}")


async def test_search_action(tool: SpellsSpecialistTool, verbose: bool = False):
    """Test the search action with various queries"""
    print_section("Testing SEARCH Action")
    
    test_cases = [
        {"query": "radial menu", "focus": "components"},
        {"query": "how to create custom spell", "focus": "creating"},
        {"query": "keyboard shortcuts", "focus": "activation"},
        {"query": "spell lifecycle", "focus": "lifecycle"},
    ]
    
    for test in test_cases:
        print(f"\n--- Search: {test['query']} (focus: {test['focus']}) ---")
        
        result = await tool.handle({
            "action": "search",
            "query": test["query"],
            "focus": test["focus"]
        })
        
        # Parse the JSON response
        response = json.loads(result[0].text)
        print_result(response, verbose)


async def test_guide_action(tool: SpellsSpecialistTool, verbose: bool = False):
    """Test the guide action for implementation guidance"""
    print_section("Testing GUIDE Action")
    
    test_cases = [
        {"query": "radial menu", "focus": "components"},
        {"query": "command palette", "focus": "creating"},
        {"query": "mouse events", "focus": "activation"},
    ]
    
    for test in test_cases:
        print(f"\n--- Guide: {test['query']} (focus: {test['focus']}) ---")
        
        result = await tool.handle({
            "action": "guide",
            "query": test["query"],
            "focus": test["focus"]
        })
        
        response = json.loads(result[0].text)
        print_result(response, verbose)


async def test_troubleshoot_action(tool: SpellsSpecialistTool, verbose: bool = False):
    """Test the troubleshoot action for debugging help"""
    print_section("Testing TROUBLESHOOT Action")
    
    test_cases = [
        {"query": "spell not activating", "focus": "activation"},
        {"query": "radial menu not showing", "focus": "components"},
        {"query": "lifecycle callbacks not working", "focus": "lifecycle"},
    ]
    
    for test in test_cases:
        print(f"\n--- Troubleshoot: {test['query']} (focus: {test['focus']}) ---")
        
        result = await tool.handle({
            "action": "troubleshoot",
            "query": test["query"],
            "focus": test["focus"]
        })
        
        response = json.loads(result[0].text)
        print_result(response, verbose)


async def test_explore_action(tool: SpellsSpecialistTool, verbose: bool = False):
    """Test the explore action for discovering features"""
    print_section("Testing EXPLORE Action")
    
    test_cases = [
        {"query": "interactive features", "focus": "general"},
        {"query": "UI components", "focus": "components"},
        {"query": "gesture controls", "focus": "activation"},
    ]
    
    for test in test_cases:
        print(f"\n--- Explore: {test['query']} (focus: {test['focus']}) ---")
        
        result = await tool.handle({
            "action": "explore",
            "query": test["query"],
            "focus": test["focus"]
        })
        
        response = json.loads(result[0].text)
        print_result(response, verbose)


async def test_edge_cases(tool: SpellsSpecialistTool, verbose: bool = False):
    """Test edge cases and error handling"""
    print_section("Testing Edge Cases")
    
    # Test with empty query
    print("\n--- Test: Empty query ---")
    result = await tool.handle({
        "action": "search",
        "query": "",
        "focus": "general"
    })
    response = json.loads(result[0].text)
    print_result(response, verbose)
    
    # Test with invalid action
    print("\n--- Test: Invalid action ---")
    result = await tool.handle({
        "action": "invalid_action",
        "query": "test",
        "focus": "general"
    })
    response = json.loads(result[0].text)
    print_result(response, verbose)
    
    # Test with missing parameters
    print("\n--- Test: Missing focus (should use default) ---")
    result = await tool.handle({
        "action": "search",
        "query": "spells"
    })
    response = json.loads(result[0].text)
    print_result(response, verbose)


async def main():
    """Main test function"""
    print("="*60)
    print("  SPELLS SPECIALIST TOOL TEST SUITE")
    print("="*60)
    
    # Parse command line arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    if verbose:
        print("Running in VERBOSE mode (full JSON output)")
    else:
        print("Running in SUMMARY mode (use --verbose for full output)")
    
    # Create mock docs index
    mock_docs = MockDocsIndex()
    
    # Create the tool instance
    tool = SpellsSpecialistTool(mock_docs)
    
    # Verify tool metadata
    print_section("Tool Metadata")
    tool_info = tool.list_tool()
    print(f"Tool Name: {tool_info.name}")
    print(f"Description: {tool_info.description}")
    print(f"Actions: {tool_info.inputSchema['properties']['action']['enum']}")
    print(f"Focus Areas: {tool_info.inputSchema['properties']['focus']['enum']}")
    
    # Run all tests
    await test_search_action(tool, verbose)
    await test_guide_action(tool, verbose)
    await test_troubleshoot_action(tool, verbose)
    await test_explore_action(tool, verbose)
    await test_edge_cases(tool, verbose)
    
    print_section("Test Suite Complete!")
    print("✅ All tests executed successfully")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())