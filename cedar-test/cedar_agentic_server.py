# src/cedar_integration_helper.py
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    import mcp.server.stdio
    import mcp.types as types
    from mcp.server import Server
    from pydantic import AnyUrl
except ImportError as e:
    print(f"❌ Missing dependency: {e}", file=sys.stderr)
    print("💡 Install with: pip install mcp>=1.2.0 pydantic>=2.0.0", file=sys.stderr)
    sys.exit(1)

# Configure logging to stderr (not stdout for MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


@dataclass
class CedarComponent:
    name: str
    description: str
    setup_steps: List[str]
    dependencies: List[str]
    code_examples: Dict[str, str]
    documentation_url: str
    integration_complexity: str  # easy, medium, hard


@dataclass
class IntegrationStep:
    step_number: int
    title: str
    description: str
    code_example: Optional[str] = None
    documentation_ref: Optional[str] = None
    prerequisites: List[str] = None


class CedarIntegrationHelper:
    """Helper for integrating Cedar-OS into applications"""
    
    def __init__(self):
        self.cedar_components = self._initialize_cedar_components()
        self.integration_guides = self._initialize_integration_guides()
        self.troubleshooting_db = self._initialize_troubleshooting()
        
    def _initialize_cedar_components(self) -> Dict[str, CedarComponent]:
        """Initialize Cedar-OS component knowledge base"""
        return {
            "agentic_state": CedarComponent(
                name="Agentic State",
                description="Central state management for AI agents and workflows",
                setup_steps=[
                    "Install Cedar-OS core package",
                    "Initialize CedarProvider in your app root",
                    "Configure state management",
                    "Set up agent connections"
                ],
                dependencies=["@cedar-os/core", "@cedar-os/state"],
                code_examples={
                    "basic_setup": """
import { CedarProvider, useAgenticState } from '@cedar-os/core';

function App() {
  return (
    <CedarProvider>
      <YourApp />
    </CedarProvider>
  );
}

function YourComponent() {
  const { agents, updateAgent } = useAgenticState();
  
  return (
    <div>
      {agents.map(agent => (
        <AgentStatus key={agent.id} agent={agent} />
      ))}
    </div>
  );
}
""",
                    "advanced_setup": """
import { CedarProvider, AgenticStateConfig } from '@cedar-os/core';

const config: AgenticStateConfig = {
  agents: {
    chat: { capabilities: ['conversation', 'context'] },
    workflow: { capabilities: ['orchestration', 'coordination'] }
  },
  persistence: true,
  realTimeUpdates: true
};

function App() {
  return (
    <CedarProvider config={config}>
      <YourApp />
    </CedarProvider>
  );
}
"""
                },
                documentation_url="https://docs.cedarcopilot.com/agentic-state/agentic-state",
                integration_complexity="medium"
            ),
            
            "chat_system": CedarComponent(
                name="Chat System",
                description="AI-powered chat interface with streaming and tool integration",
                setup_steps=[
                    "Install Cedar chat components",
                    "Configure chat provider",
                    "Set up streaming endpoints",
                    "Integrate with your backend"
                ],
                dependencies=["@cedar-os/chat", "@cedar-os/streaming"],
                code_examples={
                    "basic_chat": """
import { ChatProvider, ChatWindow } from '@cedar-os/chat';

function ChatApp() {
  return (
    <ChatProvider 
      apiEndpoint="/api/cedar/chat"
      streaming={true}
    >
      <ChatWindow 
        placeholder="Ask me anything..."
        position="floating"
      />
    </ChatProvider>
  );
}
""",
                    "custom_chat": """
import { useChat, ChatMessage } from '@cedar-os/chat';

function CustomChat() {
  const { messages, sendMessage, isLoading } = useChat();
  
  return (
    <div className="chat-container">
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
"""
                },
                documentation_url="https://docs.cedarcopilot.com/chat/chat-overview",
                integration_complexity="easy"
            ),
            
            "agent_backend": CedarComponent(
                name="Agent Backend Connection",
                description="Connect to AI backends like Mastra for agent orchestration",
                setup_steps=[
                    "Install backend adapters",
                    "Configure agent connections",
                    "Set up Mastra integration",
                    "Configure tool calling"
                ],
                dependencies=["@cedar-os/agents", "@mastra/core"],
                code_examples={
                    "mastra_integration": """
import { MastraAdapter } from '@cedar-os/agents';
import { Mastra } from '@mastra/core';

const mastra = new Mastra({
  agents: {
    assistant: {
      instructions: "You are a helpful assistant",
      model: { provider: 'openai', name: 'gpt-4' }
    }
  }
});

const cedarAgent = new MastraAdapter({
  mastra,
  agentId: 'assistant'
});

// Use in Cedar
<CedarProvider agents={{ assistant: cedarAgent }}>
  <App />
</CedarProvider>
""",
                    "custom_backend": """
import { AgentAdapter } from '@cedar-os/agents';

class CustomBackend extends AgentAdapter {
  async sendMessage(message: string) {
    const response = await fetch('/your-ai-endpoint', {
      method: 'POST',
      body: JSON.stringify({ message })
    });
    return response.json();
  }
  
  async *streamMessage(message: string) {
    // Implement streaming logic
    yield* streamingResponse;
  }
}
"""
                },
                documentation_url="https://docs.cedarcopilot.com/getting-started/connecting-to-an-agent",
                integration_complexity="hard"
            ),
            
            "voice_integration": CedarComponent(
                name="Voice Integration",
                description="Voice-powered agent interactions (Beta)",
                setup_steps=[
                    "Install voice components",
                    "Configure speech recognition",
                    "Set up voice synthesis",
                    "Integrate with agents"
                ],
                dependencies=["@cedar-os/voice"],
                code_examples={
                    "basic_voice": """
import { VoiceProvider, VoiceButton } from '@cedar-os/voice';

function VoiceApp() {
  return (
    <VoiceProvider>
      <VoiceButton 
        onTranscript={(text) => console.log('User said:', text)}
        onResponse={(audio) => console.log('AI responded')}
      />
    </VoiceProvider>
  );
}
"""
                },
                documentation_url="https://docs.cedarcopilot.com/voice-beta/voice-integration-beta",
                integration_complexity="medium"
            )
        }
    
    def _initialize_integration_guides(self) -> Dict[str, List[IntegrationStep]]:
        """Initialize step-by-step integration guides"""
        return {
            "getting_started": [
                IntegrationStep(
                    step_number=1,
                    title="Install Cedar-OS",
                    description="Add Cedar-OS to your project",
                    code_example="npm install @cedar-os/core @cedar-os/chat",
                    prerequisites=["Node.js 18+", "React 18+"]
                ),
                IntegrationStep(
                    step_number=2,
                    title="Set up Provider",
                    description="Wrap your app with CedarProvider",
                    code_example="""
import { CedarProvider } from '@cedar-os/core';

function App() {
  return (
    <CedarProvider>
      <YourApp />
    </CedarProvider>
  );
}""",
                    documentation_ref="https://docs.cedarcopilot.com/getting-started/getting-started"
                ),
                IntegrationStep(
                    step_number=3,
                    title="Add Chat Interface",
                    description="Integrate the chat system",
                    code_example="""
import { ChatWindow } from '@cedar-os/chat';

function YourApp() {
  return (
    <div>
      <YourContent />
      <ChatWindow position="floating" />
    </div>
  );
}""",
                    prerequisites=["CedarProvider setup"]
                ),
                IntegrationStep(
                    step_number=4,
                    title="Configure Backend",
                    description="Connect to your AI backend",
                    code_example="""
// Set up API endpoint
<CedarProvider 
  config={{
    apiEndpoint: '/api/cedar',
    streaming: true
  }}
>
""",
                    documentation_ref="https://docs.cedarcopilot.com/getting-started/agent-backend-connection"
                )
            ],
            
            "next_js_integration": [
                IntegrationStep(
                    step_number=1,
                    title="Install in Next.js Project",
                    description="Add Cedar-OS to your Next.js app",
                    code_example="npm install @cedar-os/core @cedar-os/chat @cedar-os/nextjs",
                    prerequisites=["Next.js 13+", "App Router"]
                ),
                IntegrationStep(
                    step_number=2,
                    title="Create API Route",
                    description="Set up the Cedar API endpoint",
                    code_example="""
// app/api/cedar/route.ts
import { CedarHandler } from '@cedar-os/nextjs';

export const POST = CedarHandler({
  agents: {
    assistant: {
      provider: 'openai',
      model: 'gpt-4'
    }
  }
});""",
                    documentation_ref="https://docs.cedarcopilot.com/backend-integration"
                ),
                IntegrationStep(
                    step_number=3,
                    title="Client-side Setup",
                    description="Configure Cedar on the client",
                    code_example="""
// app/layout.tsx
import { CedarProvider } from '@cedar-os/core';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <CedarProvider apiEndpoint="/api/cedar">
          {children}
        </CedarProvider>
      </body>
    </html>
  );
}"""
                )
            ]
        }
    
    def _initialize_troubleshooting(self) -> Dict[str, Dict]:
        """Initialize troubleshooting knowledge base"""
        return {
            "streaming_not_working": {
                "problem": "Chat streaming is not working",
                "symptoms": ["Messages appear all at once", "No typing indicator", "SSE errors"],
                "solutions": [
                    "Check if your API endpoint supports streaming",
                    "Verify Content-Type headers are set correctly",
                    "Ensure your backend returns proper SSE format",
                    "Check network tab for streaming response"
                ],
                "code_fix": """
// Backend fix - ensure proper streaming
export async function POST(req: Request) {
  return new Response(
    new ReadableStream({
      start(controller) {
        // Stream chunks here
        controller.enqueue('data: {"content": "Hello"}\n\n');
      }
    }),
    {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache'
      }
    }
  );
}"""
            },
            
            "agents_not_connecting": {
                "problem": "Agents are not connecting to backend",
                "symptoms": ["Agent status shows disconnected", "No responses from chat", "Console errors"],
                "solutions": [
                    "Verify API endpoint configuration",
                    "Check authentication setup", 
                    "Validate agent configuration",
                    "Review network connectivity"
                ],
                "code_fix": """
// Check agent configuration
<CedarProvider 
  config={{
    apiEndpoint: '/api/cedar', // Verify this endpoint exists
    agents: {
      chat: { 
        enabled: true,
        timeout: 30000 // Add timeout
      }
    }
  }}
>"""
            },
            
            "state_not_persisting": {
                "problem": "Agentic state is not persisting between sessions",
                "symptoms": ["State resets on page reload", "Lost conversation history"],
                "solutions": [
                    "Enable persistence in Cedar config",
                    "Set up proper storage backend",
                    "Configure session management",
                    "Check localStorage/sessionStorage"
                ],
                "code_fix": """
<CedarProvider 
  config={{
    persistence: {
      enabled: true,
      storage: 'localStorage', // or 'sessionStorage'
      key: 'cedar-state'
    }
  }}
>"""
            }
        }


class CedarIntegrationMCPServer:
    """MCP Server to help developers integrate Cedar-OS into their applications"""
    
    def __init__(self):
        self.helper = CedarIntegrationHelper()
        self.server = Server("cedar-integration-helper")
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP request handlers for Cedar integration help"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List all available Cedar integration tools"""
            return [
                types.Tool(
                    name="cedar_get_component_info",
                    description="Get detailed information about Cedar-OS components and how to integrate them",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component": {
                                "type": "string",
                                "enum": ["agentic_state", "chat_system", "agent_backend", "voice_integration", "all"],
                                "description": "Cedar component to get information about"
                            },
                            "include_examples": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include code examples"
                            }
                        },
                        "required": ["component"]
                    }
                ),
                types.Tool(
                    name="cedar_get_integration_guide",
                    description="Get step-by-step integration guide for your specific setup",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "framework": {
                                "type": "string",
                                "enum": ["react", "next_js", "vite", "getting_started"],
                                "description": "Your app framework",
                                "default": "getting_started"
                            },
                            "components": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Cedar components you want to integrate",
                                "default": ["chat_system"]
                            }
                        }
                    }
                ),
                types.Tool(
                    name="cedar_troubleshoot_issue",
                    description="Get help troubleshooting Cedar-OS integration issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue": {
                                "type": "string",
                                "description": "Describe the issue you're experiencing"
                            },
                            "component": {
                                "type": "string",
                                "enum": ["chat_system", "agentic_state", "agent_backend", "voice_integration", "general"],
                                "description": "Which Cedar component is having issues"
                            },
                            "error_message": {
                                "type": "string",
                                "description": "Any error messages you're seeing"
                            }
                        },
                        "required": ["issue"]
                    }
                ),
                types.Tool(
                    name="cedar_generate_setup_code",
                    description="Generate boilerplate code for Cedar-OS integration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "framework": {
                                "type": "string",
                                "enum": ["react", "next_js", "vite"],
                                "description": "Your app framework"
                            },
                            "components": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["chat_system", "agentic_state", "agent_backend", "voice_integration"]
                                },
                                "description": "Cedar components to include"
                            },
                            "styling": {
                                "type": "string",
                                "enum": ["tailwind", "css_modules", "styled_components", "none"],
                                "default": "tailwind"
                            }
                        },
                        "required": ["framework", "components"]
                    }
                ),
                types.Tool(
                    name="cedar_check_compatibility",
                    description="Check if your current setup is compatible with Cedar-OS",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dependencies": {
                                "type": "object",
                                "description": "Your current package.json dependencies"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Your app framework and version"
                            },
                            "node_version": {
                                "type": "string",
                                "description": "Your Node.js version"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="cedar_explain_concept",
                    description="Explain Cedar-OS concepts and architecture",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "concept": {
                                "type": "string",
                                "enum": [
                                    "agentic_state",
                                    "agent_orchestration", 
                                    "mastra_integration",
                                    "streaming_chat",
                                    "voice_integration",
                                    "diff_history",
                                    "spells",
                                    "cedar_architecture"
                                ],
                                "description": "Cedar concept to explain"
                            },
                            "detail_level": {
                                "type": "string",
                                "enum": ["basic", "intermediate", "advanced"],
                                "default": "intermediate"
                            }
                        },
                        "required": ["concept"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls for Cedar integration help"""
            try:
                if name == "cedar_get_component_info":
                    return await self.get_component_info(
                        arguments.get("component"),
                        arguments.get("include_examples", True)
                    )
                elif name == "cedar_get_integration_guide":
                    return await self.get_integration_guide(
                        arguments.get("framework", "getting_started"),
                        arguments.get("components", ["chat_system"])
                    )
                elif name == "cedar_troubleshoot_issue":
                    return await self.troubleshoot_issue(
                        arguments.get("issue"),
                        arguments.get("component"),
                        arguments.get("error_message")
                    )
                elif name == "cedar_generate_setup_code":
                    return await self.generate_setup_code(
                        arguments.get("framework"),
                        arguments.get("components"),
                        arguments.get("styling", "tailwind")
                    )
                elif name == "cedar_check_compatibility":
                    return await self.check_compatibility(
                        arguments.get("dependencies"),
                        arguments.get("framework"),
                        arguments.get("node_version")
                    )
                elif name == "cedar_explain_concept":
                    return await self.explain_concept(
                        arguments.get("concept"),
                        arguments.get("detail_level", "intermediate")
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )]

        @self.server.list_resources()
        async def handle_list_resources() -> List[types.Resource]:
            """List Cedar integration resources"""
            return [
                types.Resource(
                    uri=AnyUrl("cedar://docs/components"),
                    name="Cedar Components Documentation",
                    description="Complete guide to all Cedar-OS components",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri=AnyUrl("cedar://examples/integration"),
                    name="Integration Examples",
                    description="Code examples for different frameworks",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri=AnyUrl("cedar://troubleshooting/common"),
                    name="Common Issues",
                    description="Troubleshooting guide for common integration issues",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri=AnyUrl("cedar://setup/quickstart"),
                    name="Quick Start Guide",
                    description="Get started with Cedar-OS in 5 minutes",
                    mimeType="text/markdown"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            """Handle resource reads for Cedar integration help"""
            uri_str = str(uri)
            
            if uri_str == "cedar://docs/components":
                return json.dumps(self.helper.cedar_components, default=asdict, indent=2)
            elif uri_str == "cedar://examples/integration":
                examples = {}
                for comp_name, comp in self.helper.cedar_components.items():
                    examples[comp_name] = comp.code_examples
                return json.dumps(examples, indent=2)
            elif uri_str == "cedar://troubleshooting/common":
                return json.dumps(self.helper.troubleshooting_db, indent=2)
            elif uri_str == "cedar://setup/quickstart":
                return self.generate_quickstart_guide()
            else:
                raise ValueError(f"Unknown resource: {uri}")

    # Tool implementation methods
    async def get_component_info(self, component: str, include_examples: bool = True) -> List[types.TextContent]:
        """Get information about Cedar-OS components"""
        
        if component == "all":
            result = {
                "components": {},
                "summary": f"Cedar-OS has {len(self.helper.cedar_components)} main components"
            }
            
            for name, comp in self.helper.cedar_components.items():
                comp_info = {
                    "name": comp.name,
                    "description": comp.description,
                    "complexity": comp.integration_complexity,
                    "dependencies": comp.dependencies,
                    "documentation": comp.documentation_url
                }
                
                if include_examples:
                    comp_info["examples"] = comp.code_examples
                
                result["components"][name] = comp_info
        
        elif component in self.helper.cedar_components:
            comp = self.helper.cedar_components[component]
            result = {
                "component": comp.name,
                "description": comp.description,
                "integration_complexity": comp.integration_complexity,
                "setup_steps": comp.setup_steps,
                "dependencies": comp.dependencies,
                "documentation_url": comp.documentation_url
            }
            
            if include_examples:
                result["code_examples"] = comp.code_examples
        
        else:
            available = list(self.helper.cedar_components.keys())
            result = {
                "error": f"Unknown component: {component}",
                "available_components": available
            }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def get_integration_guide(self, framework: str, components: List[str]) -> List[types.TextContent]:
        """Get step-by-step integration guide"""
        
        if framework == "getting_started":
            guide = self.helper.integration_guides["getting_started"]
        elif framework == "next_js":
            guide = self.helper.integration_guides["next_js_integration"]
        else:
            # Generate guide for other frameworks
            guide = self.generate_framework_guide(framework, components)
        
        result = {
            "framework": framework,
            "components": components,
            "steps": []
        }
        
        for step in guide:
            step_data = {
                "step": step.step_number,
                "title": step.title,
                "description": step.description,
                "prerequisites": step.prerequisites or []
            }
            
            if step.code_example:
                step_data["code"] = step.code_example
            
            if step.documentation_ref:
                step_data["docs"] = step.documentation_ref
            
            result["steps"].append(step_data)
        
        # Add component-specific steps
        for component in components:
            if component in self.helper.cedar_components:
                comp = self.helper.cedar_components[component]
                result[f"{component}_setup"] = {
                    "dependencies": comp.dependencies,
                    "setup_steps": comp.setup_steps,
                    "examples": comp.code_examples
                }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def troubleshoot_issue(self, issue: str, component: str = None, error_message: str = None) -> List[types.TextContent]:
        """Help troubleshoot Cedar integration issues"""
        
        # Match issue to known problems
        matched_solutions = []
        
        for problem_key, problem_data in self.helper.troubleshooting_db.items():
            # Simple keyword matching - in real implementation, use better NLP
            if any(keyword in issue.lower() for keyword in problem_data["problem"].lower().split()):
                matched_solutions.append({
                    "problem": problem_data["problem"],
                    "symptoms": problem_data["symptoms"],
                    "solutions": problem_data["solutions"],
                    "code_fix": problem_data.get("code_fix", "")
                })
        
        result = {
            "issue_description": issue,
            "component": component,
            "error_message": error_message,
            "matched_solutions": matched_solutions
        }
        
        if not matched_solutions:
            result["general_debugging_steps"] = [
                "Check browser console for errors",
                "Verify all Cedar dependencies are installed",
                "Check that CedarProvider is properly configured",
                "Ensure API endpoints are accessible",
                "Review Cedar documentation for the component"
            ]
            
            result["helpful_resources"] = [
                "https://docs.cedarcopilot.com/troubleshooting",
                "Cedar Discord community", 
                "GitHub issues for specific bugs"
            ]
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def generate_setup_code(self, framework: str, components: List[str], styling: str = "tailwind") -> List[types.TextContent]:
        """Generate boilerplate setup code"""
        
        result = {
            "framework": framework,
            "components": components,
            "styling": styling,
            "files": {}
        }
        
        # Generate package.json dependencies
        dependencies = ["@cedar-os/core"]
        for comp in components:
            if comp in self.helper.cedar_components:
                dependencies.extend(self.helper.cedar_components[comp].dependencies)
        
        result["package_json_additions"] = {
            "dependencies": {dep: "latest" for dep in set(dependencies)}
        }
        
        # Generate main app setup
        if framework == "next_js":
            result["files"]["app/layout.tsx"] = self.generate_nextjs_layout(components)
            result["files"]["app/api/cedar/route.ts"] = self.generate_nextjs_api()
        elif framework == "react":
            result["files"]["src/App.tsx"] = self.generate_react_app(components)
        
        # Generate component examples
        for comp in components:
            if comp == "chat_system":
                result["files"][f"components/CedarChat.tsx"] = self.generate_chat_component(styling)
            elif comp == "agentic_state":
                result["files"][f"components/AgentStatus.tsx"] = self.generate_agent_status_component(styling)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def check_compatibility(self, dependencies: dict = None, framework: str = None, node_version: str = None) -> List[types.TextContent]:
        """Check compatibility with Cedar-OS"""
        
        result = {
            "compatible": True,
            "issues": [],
            "recommendations": []
        }
        
        # Check Node.js version
        if node_version:
            if node_version.startswith("v"):
                version_num = node_version[1:]
            else:
                version_num = node_version
                
            major_version = int(version_num.split(".")[0])
            if major_version < 18:
                result["compatible"] = False
                result["issues"].append(f"Node.js {version_num} is too old. Cedar-OS requires Node.js 18+")
                result["recommendations"].append("Upgrade to Node.js 18 or later")
        
        # Check React version
        if dependencies and "react" in dependencies:
            react_version = dependencies["react"]
            if react_version.startswith("^") or react_version.startswith("~"):
                react_version = react_version[1:]
            
            major_version = int(react_version.split(".")[0])
            if major_version < 18:
                result["issues"].append(f"React {react_version} may have compatibility issues. Cedar-OS is tested with React 18+")
                result["recommendations"].append("Consider upgrading to React 18+")
        
        # Check for conflicting dependencies
        if dependencies:
            conflicts = {
                "react-router": "Cedar works best with Next.js App Router or React Router v6+",
                "emotion": "Cedar uses its own styling system, Emotion may conflict"
            }
            
            for dep, warning in conflicts.items():
                if dep in dependencies:
                    result["recommendations"].append(warning)
        
        # Framework-specific checks
        if framework:
            if "next" in framework.lower():
                result["recommendations"].append("Great choice! Cedar-OS has excellent Next.js support")
            elif "vite" in framework.lower():
                result["recommendations"].append("Vite is supported. Make sure to configure SSR properly for Cedar components")
        
        if result["compatible"]:
            result["message"] = "Your setup looks compatible with Cedar-OS!"
        else:
            result["message"] = "Some compatibility issues found. Please review recommendations."
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def explain_concept(self, concept: str, detail_level: str = "intermediate") -> List[types.TextContent]:
        """Explain Cedar-OS concepts and architecture"""
        
        explanations = {
            "agentic_state": {
                "basic": "Agentic State is Cedar's way of managing AI agent status and coordination. Think of it as a central dashboard that tracks what each AI agent is doing.",
                "intermediate": "Agentic State provides centralized state management for AI agents, workflows, and user context. It enables real-time coordination between multiple agents and maintains consistency across your application. Agents can read and write to shared state, enabling sophisticated multi-agent workflows.",
                "advanced": "Agentic State implements a reactive state management pattern specifically designed for AI agent coordination. It uses event-driven updates, conflict resolution, and state persistence to manage complex agent interactions. The state is partitioned into agent-specific, workflow-specific, and global contexts, with fine-grained subscription capabilities for optimal performance."
            },
            
            "agent_orchestration": {
                "basic": "Agent orchestration is how Cedar coordinates multiple AI agents to work together on complex tasks.",
                "intermediate": "Agent orchestration in Cedar enables multiple specialized AI agents to collaborate on complex tasks. A workflow agent acts as a conductor, breaking down user requests into subtasks and assigning them to appropriate agents (chat, content, UI, etc.). This creates seamless user experiences from complex multi-agent coordination.",
                "advanced": "Cedar's agent orchestration implements hierarchical task decomposition with dependency management, resource allocation, and dynamic load balancing. It supports sequential, parallel, and hybrid execution patterns with rollback capabilities. The orchestration layer handles agent lifecycle management, inter-agent communication, and failure recovery."
            },
            
            "mastra_integration": {
                "basic": "Mastra is Cedar's backend framework for AI workflows. It connects Cedar's frontend to powerful AI models and tools.",
                "intermediate": "Mastra integration provides Cedar with a robust backend for AI agent management. Mastra handles LLM connections, tool calling, workflow execution, and agent memory. Cedar components connect to Mastra through adapters, enabling seamless frontend-backend coordination for AI-powered applications.",
                "advanced": "The Cedar-Mastra integration implements a clean separation between presentation and AI logic. Mastra's workflow engine provides durable execution with state persistence, while Cedar's frontend components provide reactive UIs. The integration supports real-time streaming, tool calling, and complex multi-step workflows with proper error handling and observability."
            },
            
            "streaming_chat": {
                "basic": "Streaming chat shows AI responses as they're being generated, character by character, creating a more natural conversation experience.",
                "intermediate": "Cedar's streaming chat implements Server-Sent Events (SSE) to deliver AI responses in real-time. As the AI generates text, chunks are streamed to the frontend and displayed progressively. This creates responsive user experiences and allows for interruption and real-time interaction.",
                "advanced": "The streaming implementation uses SSE with proper backpressure handling, connection recovery, and state synchronization. It supports tool calling during streams, partial response validation, and graceful degradation. The frontend handles token buffering, typing indicators, and seamless integration with Cedar's agent state management."
            },
            
            "voice_integration": {
                "basic": "Voice integration lets users talk to AI agents using speech instead of typing.",
                "intermediate": "Cedar's voice integration combines speech recognition, AI processing, and speech synthesis for natural voice conversations. It handles audio capture, transcription, agent processing, and audio playback while maintaining context and state consistency.",
                "advanced": "The voice system implements real-time audio processing with noise cancellation, speaker identification, and emotion detection. It supports interruption handling, multi-turn conversations, and integration with the broader agent ecosystem for voice-triggered workflows."
            },
            
            "cedar_architecture": {
                "basic": "Cedar is built with a component-based architecture where UI components connect to AI agents through a central state management system.",
                "intermediate": "Cedar's architecture separates concerns between UI components, agent coordination, and backend integration. The frontend uses React components with hooks for agent interaction, while the backend integrates with various AI providers through adapters. Central state management ensures consistency across all components.",
                "advanced": "Cedar implements a layered architecture with clear separation between presentation, coordination, and integration layers. The component layer provides reusable UI primitives, the coordination layer manages agent workflows and state, and the integration layer connects to various AI backends. The architecture supports plugin-based extensions, custom agents, and framework-agnostic integration patterns."
            }
        }
        
        explanation = explanations.get(concept, {}).get(detail_level, f"No explanation available for {concept} at {detail_level} level")
        
        result = {
            "concept": concept,
            "detail_level": detail_level,
            "explanation": explanation
        }
        
        # Add related concepts
        related_concepts = {
            "agentic_state": ["agent_orchestration", "mastra_integration"],
            "agent_orchestration": ["agentic_state", "cedar_architecture"],
            "mastra_integration": ["agent_orchestration", "streaming_chat"],
            "streaming_chat": ["mastra_integration", "voice_integration"],
            "voice_integration": ["streaming_chat", "agentic_state"],
            "cedar_architecture": ["agentic_state", "agent_orchestration"]
        }
        
        if concept in related_concepts:
            result["related_concepts"] = related_concepts[concept]
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    # Helper methods for code generation
    def generate_nextjs_layout(self, components: List[str]) -> str:
        imports = ["import { CedarProvider } from '@cedar-os/core';"]
        if "chat_system" in components:
            imports.append("import { ChatProvider } from '@cedar-os/chat';")
        if "voice_integration" in components:
            imports.append("import { VoiceProvider } from '@cedar-os/voice';")
        
        providers = ["<CedarProvider apiEndpoint='/api/cedar'>"]
        if "chat_system" in components:
            providers.append("  <ChatProvider>")
        if "voice_integration" in components:
            providers.append("    <VoiceProvider>")
        
        providers.append("      {children}")
        
        if "voice_integration" in components:
            providers.append("    </VoiceProvider>")
        if "chat_system" in components:
            providers.append("  </ChatProvider>")
        providers.append("</CedarProvider>")
        
        return f"""
{chr(10).join(imports)}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body>
        {chr(10).join(providers)}
      </body>
    </html>
  )
}}
"""

    def generate_nextjs_api(self) -> str:
        return """
import { CedarHandler } from '@cedar-os/nextjs';

export const POST = CedarHandler({
  agents: {
    assistant: {
      provider: 'openai',
      model: 'gpt-4',
      instructions: 'You are a helpful assistant integrated with Cedar-OS'
    }
  },
  streaming: true
});
"""

    def generate_react_app(self, components: List[str]) -> str:
        imports = ["import { CedarProvider } from '@cedar-os/core';"]
        if "chat_system" in components:
            imports.append("import { ChatWindow } from '@cedar-os/chat';")
        
        components_jsx = []
        if "chat_system" in components:
            components_jsx.append("      <ChatWindow position='floating' />")
        
        return f"""
{chr(10).join(imports)}

function App() {{
  return (
    <CedarProvider apiEndpoint='/api/cedar'>
      <div className="App">
        <h1>My Cedar-OS App</h1>
{chr(10).join(components_jsx)}
      </div>
    </CedarProvider>
  );
}}

export default App;
"""

    def generate_chat_component(self, styling: str) -> str:
        if styling == "tailwind":
            styles = {
                "container": "fixed bottom-4 right-4 w-80 h-96 bg-white rounded-lg shadow-lg",
                "messages": "flex-1 p-4 overflow-y-auto",
                "input": "border-t p-4"
            }
        else:
            styles = {
                "container": "chat-container",
                "messages": "chat-messages", 
                "input": "chat-input"
            }
        
        return f"""
import {{ useChat }} from '@cedar-os/chat';

export function CedarChat() {{
  const {{ messages, sendMessage, isLoading }} = useChat();
  
  return (
    <div className="{styles['container']}">
      <div className="{styles['messages']}">
        {{messages.map(msg => (
          <div key={{msg.id}} className="mb-2">
            <strong>{{msg.role}}:</strong> {{msg.content}}
          </div>
        ))}}
      </div>
      <div className="{styles['input']}">
        <input 
          placeholder="Type a message..."
          onKeyPress={{(e) => {{
            if (e.key === 'Enter') {{
              sendMessage(e.target.value);
              e.target.value = '';
            }}
          }}}}
        />
      </div>
    </div>
  );
}}
"""

    def generate_agent_status_component(self, styling: str) -> str:
        return """
import { useAgenticState } from '@cedar-os/core';

export function AgentStatus() {
  const { agents } = useAgenticState();
  
  return (
    <div className="agent-status">
      <h3>Agent Status</h3>
      {agents.map(agent => (
        <div key={agent.id} className="agent-item">
          <span className={`status-${agent.status}`}>
            {agent.name}: {agent.status}
          </span>
        </div>
      ))}
    </div>
  );
}
"""

    def generate_framework_guide(self, framework: str, components: List[str]) -> List[IntegrationStep]:
        """Generate integration guide for specific framework"""
        return [
            IntegrationStep(
                step_number=1,
                title=f"Set up {framework} project",
                description=f"Initialize your {framework} project with Cedar-OS dependencies",
                code_example=f"npx create-{framework}-app my-cedar-app\ncd my-cedar-app\nnpm install @cedar-os/core"
            ),
            IntegrationStep(
                step_number=2,
                title="Configure Cedar Provider",
                description="Set up the main Cedar provider component",
                code_example="// See generated code for your specific setup"
            )
        ]

    def generate_quickstart_guide(self) -> str:
        return """
# Cedar-OS Quick Start Guide

## 1. Installation
```bash
npm install @cedar-os/core @cedar-os/chat
```

## 2. Basic Setup
```tsx
import { CedarProvider, ChatWindow } from '@cedar-os/core';

function App() {
  return (
    <CedarProvider apiEndpoint="/api/cedar">
      <YourApp />
      <ChatWindow position="floating" />
    </CedarProvider>
  );
}
```

## 3. Backend Setup (Next.js)
```tsx
// app/api/cedar/route.ts
import { CedarHandler } from '@cedar-os/nextjs';

export const POST = CedarHandler({
  agents: {
    assistant: { provider: 'openai', model: 'gpt-4' }
  }
});
```

## 4. Start Building!
Your Cedar-OS integration is ready. The chat interface will connect to your AI backend automatically.

For more detailed guides, use the MCP tools:
- `cedar_get_integration_guide`
- `cedar_get_component_info`
- `cedar_generate_setup_code`
"""


async def main():
    """Main entry point"""
    server_instance = CedarIntegrationMCPServer()
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("🌳 Cedar Integration Helper MCP Server starting...")
        logger.info("📚 Ready to help with Cedar-OS integration!")
        logger.info("🛠️  Available tools: component info, integration guides, troubleshooting, code generation")
        
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())