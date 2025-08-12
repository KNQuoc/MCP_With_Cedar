from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex


class VoiceSpecialistTool:
    """Specialized tool for Cedar-OS Voice feature development"""
    
    name = "voiceSpecialist"
    
    # Voice-specific keywords for focused search (from Cedar docs)
    VOICE_KEYWORDS = [
        "voice", "voicestate", "voiceindicator", "microphone", "mic",
        "speech", "audio", "recording", "transcription", "realtime",
        "whisper", "voicebutton", "voicestatuspanel", "voicesettings",
        "islistening", "isspeaking", "voicepermissionstatus", "voiceendpoint",
        "startlistening", "stoplistening", "togglevoice", "updatevoicesettings",
        "voiceerror", "voicewaveform", "voice toggle", "voice interface"
    ]
    
    # Common voice implementation patterns (from Cedar docs)
    VOICE_PATTERNS = {
        "basic_setup": """
// Basic Voice Setup Pattern (from Cedar docs)
1. Install Cedar-OS using 'npx cedar-os-cli plant-seed'
2. Voice features work automatically in ChatInput
3. Press 'M' key to toggle voice (when not typing)
4. Mic button shows red pulsing when recording
5. VoiceIndicator appears when voice.isListening is true
""",
        "voice_button": """
// Voice Button States (from Cedar docs)
- Red pulsing animation when recording (voice.isListening)
- Green color when playing AI response (voice.isSpeaking)  
- Gray/disabled when permissions denied
- Automatic permission request on first use
- Built into ChatInput component by default
""",
        "voice_indicator": """
// VoiceIndicator Component (from Cedar docs)
- Import from '@cedar/voice'
- Pass voiceState prop from useCedarStore
- Shows smooth animated bars powered by Motion for React
- Displays real-time transcription text
- Position with className (e.g., 'absolute -top-12 right-0')
""",
        "permissions": """
// Voice Permission States (from Cedar docs)
- 'granted': Microphone access allowed
- 'denied': User blocked microphone access
- 'not-supported': Browser doesn't support voice
- 'prompt': Permission not yet requested
- ChatInput handles permissions automatically
- Use voice.requestMicrophonePermission() for manual control
"""
    }
    
    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index
    
    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="Specialized tool for Cedar-OS Voice feature development - searches voice docs, provides implementation patterns, and guides voice integration",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "implement", "troubleshoot", "patterns"],
                        "description": "Action to perform: search docs, get implementation guide, troubleshoot issues, or get patterns"
                    },
                    "query": {
                        "type": "string",
                        "description": "Specific voice-related query or component name"
                    },
                    "component": {
                        "type": "string",
                        "enum": ["VoiceIndicator", "VoiceButton", "VoiceSettings", "VoiceStatusPanel", "VoiceWaveform", "ChatInput", "general"],
                        "description": "Specific voice component to focus on"
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["nextjs", "react", "vue", "vanilla"],
                        "default": "nextjs",
                        "description": "Target framework for implementation"
                    }
                },
                "required": ["action"]
            }
        )
    
    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        action = arguments.get("action", "search")
        query = arguments.get("query", "")
        component = arguments.get("component", "general")
        framework = arguments.get("framework", "nextjs")
        
        if action == "search":
            return await self._search_voice_docs(query, component)
        elif action == "implement":
            return await self._get_implementation_guide(component, framework, query)
        elif action == "troubleshoot":
            return await self._troubleshoot_voice_issue(query, component)
        elif action == "patterns":
            return self._get_voice_patterns(component)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown action: {action}"}))]
    
    async def _search_voice_docs(self, query: str, component: str) -> List[TextContent]:
        """Search specifically for voice-related documentation"""
        # Enhance query with voice-specific terms
        enhanced_query = query
        if component != "general":
            enhanced_query = f"{component} {query}"
        
        # Add voice context to query
        voice_query = f"voice {enhanced_query} microphone audio recording transcription"
        
        # Search with both semantic and keyword matching
        results = await self.docs_index.search(voice_query, limit=10, use_semantic=True)
        
        # Filter results to prioritize voice-specific content
        voice_results = []
        for result in results:
            content_lower = result.get("content", "").lower()
            heading_lower = result.get("heading", "").lower()
            
            # Check if result is voice-related
            if any(keyword in content_lower or keyword in heading_lower 
                   for keyword in self.VOICE_KEYWORDS):
                voice_results.append(result)
        
        # If no voice-specific results, include general results
        if not voice_results:
            voice_results = results[:5]
        
        payload = {
            "action": "search",
            "component": component,
            "query": query,
            "results": voice_results[:7],  # Return top 7 voice-specific results
            "guidance": self._get_voice_guidance(component),
            "keywords_used": self.VOICE_KEYWORDS[:10]
        }
        
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]
    
    async def _get_implementation_guide(self, component: str, framework: str, query: str) -> List[TextContent]:
        """Get implementation guide for voice features"""
        # Search for relevant examples
        search_query = f"{component} {framework} implementation example code"
        docs_results = await self.docs_index.search(search_query, limit=5, use_semantic=True)
        
        # Build implementation steps
        implementation_steps = self._build_implementation_steps(component, framework)
        
        # Get relevant patterns
        patterns = self.VOICE_PATTERNS.get("basic_setup", "")
        if component == "VoiceIndicator":
            patterns = self.VOICE_PATTERNS.get("voice_indicator", "")
        elif component == "VoiceButton":
            patterns = self.VOICE_PATTERNS.get("voice_button", "")
        
        payload = {
            "action": "implement",
            "component": component,
            "framework": framework,
            "steps": implementation_steps,
            "patterns": patterns,
            "examples": docs_results[:3],
            "imports": self._get_voice_imports(component, framework),
            "configuration": self._get_voice_config(component),
            "common_issues": self._get_common_voice_issues(component)
        }
        
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]
    
    async def _troubleshoot_voice_issue(self, query: str, component: str) -> List[TextContent]:
        """Troubleshoot voice-related issues"""
        # Search for error-related documentation
        error_query = f"voice error {query} troubleshoot fix issue problem"
        docs_results = await self.docs_index.search(error_query, limit=5, use_semantic=True)
        
        # Get common solutions
        solutions = self._get_voice_solutions(query, component)
        
        payload = {
            "action": "troubleshoot",
            "issue": query,
            "component": component,
            "potential_causes": self._analyze_voice_issue(query),
            "solutions": solutions,
            "documentation": docs_results,
            "checklist": self._get_troubleshooting_checklist(component),
            "debugging_tips": self._get_debugging_tips()
        }
        
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]
    
    def _get_voice_patterns(self, component: str) -> List[TextContent]:
        """Get voice implementation patterns"""
        patterns = {}
        
        if component == "general" or component == "ChatInput":
            patterns = self.VOICE_PATTERNS
        else:
            # Get specific pattern for component
            pattern_key = {
                "VoiceIndicator": "voice_indicator",
                "VoiceButton": "voice_button",
                "VoiceSettings": "basic_setup",
                "VoiceStatus": "permissions"
            }.get(component, "basic_setup")
            patterns = {pattern_key: self.VOICE_PATTERNS.get(pattern_key, "")}
        
        payload = {
            "action": "patterns",
            "component": component,
            "patterns": patterns,
            "usage_examples": self._get_pattern_examples(component)
        }
        
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]
    
    def _get_voice_guidance(self, component: str) -> str:
        """Get component-specific guidance"""
        guidance_map = {
            "VoiceIndicator": "Visual feedback component showing voice activity with smooth animations powered by Motion for React. Shows animated bars when listening.",
            "VoiceButton": "Microphone toggle button that changes appearance based on voice state. Handles permissions and provides visual feedback (red pulsing when recording, green when playing).",
            "VoiceSettings": "Configuration panel for voice preferences including language, voice model, rate, volume, and TTS options.",
            "VoiceStatusPanel": "Comprehensive status panel showing all voice information including permissions, connection state, and error messages.",
            "VoiceWaveform": "Audio waveform visualizer component for real-time voice visualization.",
            "ChatInput": "ChatInput automatically includes voice features - mic button, keyboard shortcut (M key), and VoiceIndicator integration.",
            "general": "Cedar Voice provides WebRTC-based real-time audio with OpenAI integration for transcription (Whisper) and TTS."
        }
        return guidance_map.get(component, guidance_map["general"])
    
    def _build_implementation_steps(self, component: str, framework: str) -> List[str]:
        """Build implementation steps for a component"""
        base_steps = [
            "Install Cedar-OS using 'npx cedar-os-cli plant-seed'",
            "Configure voice endpoint in your environment",
            "Set up OpenAI API key for voice services",
        ]
        
        component_steps = {
            "VoiceIndicator": [
                "Import VoiceIndicator from '@cedar/voice'",
                "Pass voiceState prop from useCedarStore",
                "Component shows animated bars when isListening is true",
                "Displays transcription text in real-time",
                "Add className for positioning (e.g., 'absolute -top-12 right-0')"
            ],
            "VoiceButton": [
                "Import VoiceButton component or use ChatInput's built-in button",
                "Button automatically handles voice.toggleVoice()",
                "Shows red pulsing animation when recording",
                "Shows green color when playing AI response",
                "Disabled state when permissions denied",
                "M key shortcut works automatically in ChatInput"
            ],
            "VoiceSettings": [
                "Import VoiceSettings component",
                "Connect to voice.voiceSettings from useCedarStore",
                "Language selection (en-US, en-GB, es-ES, fr-FR, etc.)",
                "Voice model selection (alloy, echo, fable, onyx, nova, shimmer)",
                "Rate control (0.25 to 4.0) and volume control (0 to 1)",
                "Toggle options: autoAddToMessages, useBrowserTTS"
            ],
            "ChatInput": [
                "Use Cedar's ChatInput component",
                "Voice features are included automatically",
                "Configure voice endpoint",
                "Customize mic button appearance if needed"
            ]
        }
        
        return base_steps + component_steps.get(component, [
            "Import voice components from Cedar",
            "Configure voice state management",
            "Add UI components for voice interaction"
        ])
    
    def _get_voice_imports(self, component: str, framework: str) -> Dict[str, str]:
        """Get required imports for voice features"""
        imports = {
            "cedar_core": "import { useCedarStore } from '@cedar/core';",
            "voice_components": f"import {{ {component} }} from '@cedar/voice';" if component not in ["general", "ChatInput"] else "import { VoiceIndicator } from '@cedar/voice';",
            "chat_input": "import { ChatInput } from 'cedar-os-components';",
            "types": "import type { VoiceState, VoiceSettings } from '@cedar/types';",
            "hooks": "import { useVoice } from 'cedar-os';",
            "icons": "import { Mic, MicOff, Volume2, Settings } from 'lucide-react';" if component in ["VoiceButton", "VoiceStatusPanel"] else ""
        }
        
        if framework == "nextjs":
            imports["client"] = "'use client'; // Required for Next.js App Router"
        
        return imports
    
    def _get_voice_config(self, component: str) -> Dict[str, Any]:
        """Get voice configuration requirements"""
        return {
            "environment": {
                "OPENAI_API_KEY": "Required for transcription and voice synthesis",
                "VOICE_ENDPOINT": "WebSocket endpoint for real-time voice (optional)",
                "VOICE_MODEL": "OpenAI transcription model (default: whisper-1)"
            },
            "permissions": {
                "microphone": "Required - will prompt user automatically",
                "autoplay": "Recommended for voice responses"
            },
            "browser_support": {
                "chrome": "Full support",
                "firefox": "Full support", 
                "safari": "Requires user interaction for first audio playback",
                "edge": "Full support"
            }
        }
    
    def _get_common_voice_issues(self, component: str) -> List[Dict[str, str]]:
        """Get common issues and solutions"""
        issues = [
            {
                "issue": "Microphone permission denied",
                "solution": "Check browser settings, ensure HTTPS, handle permission denial in UI"
            },
            {
                "issue": "Voice not working in Safari",
                "solution": "Ensure user interaction before audio playback, check autoplay policies"
            },
            {
                "issue": "No audio input detected",
                "solution": "Check microphone selection, verify MediaStream constraints"
            },
            {
                "issue": "Voice endpoint connection failed",
                "solution": "Verify WebSocket URL, check CORS settings, ensure SSL for production"
            }
        ]
        
        if component == "VoiceIndicator":
            issues.append({
                "issue": "Animation not showing",
                "solution": "Check voice.isListening state, verify CSS animations are loaded"
            })
        
        return issues
    
    def _analyze_voice_issue(self, query: str) -> List[str]:
        """Analyze potential causes of voice issues"""
        query_lower = query.lower()
        causes = []
        
        if "permission" in query_lower or "denied" in query_lower:
            causes.append("Microphone permissions not granted")
            causes.append("Browser security policies blocking access")
            causes.append("Not using HTTPS in production")
        
        if "not working" in query_lower or "doesn't work" in query_lower:
            causes.append("Voice endpoint not configured")
            causes.append("API keys missing or invalid")
            causes.append("Browser compatibility issues")
            causes.append("Component not properly imported")
        
        if "no sound" in query_lower or "audio" in query_lower:
            causes.append("Audio output device issues")
            causes.append("Browser autoplay policies")
            causes.append("Volume settings muted")
        
        if not causes:
            causes = ["Configuration issue", "State management problem", "Network connectivity"]
        
        return causes
    
    def _get_voice_solutions(self, query: str, component: str) -> List[str]:
        """Get solutions for voice issues"""
        solutions = [
            "Verify Cedar-OS is properly installed with 'npx cedar-os-cli plant-seed'",
            "Check browser console for specific error messages",
            "Ensure all required environment variables are set"
        ]
        
        query_lower = query.lower()
        
        if "permission" in query_lower:
            solutions.extend([
                "Add permission request handling before voice activation",
                "Provide clear UI feedback when permissions are denied",
                "Test in incognito mode to reset permissions"
            ])
        
        if "websocket" in query_lower or "connection" in query_lower:
            solutions.extend([
                "Verify voice endpoint URL is correct",
                "Check WebSocket connection in Network tab",
                "Ensure backend supports WebSocket connections"
            ])
        
        return solutions
    
    def _get_troubleshooting_checklist(self, component: str) -> List[str]:
        """Get troubleshooting checklist"""
        return [
            "✓ Cedar-OS installed via plant-seed command",
            "✓ OpenAI API key configured and valid",
            "✓ Microphone permissions granted",
            "✓ HTTPS used in production environment",
            "✓ Voice components properly imported",
            "✓ useCedarStore hook connected",
            "✓ Browser console checked for errors",
            "✓ Network tab checked for failed requests",
            f"✓ {component} component rendered in DOM" if component != "general" else "✓ Voice components visible in UI",
            "✓ Voice state updates in Redux DevTools"
        ]
    
    def _get_debugging_tips(self) -> List[str]:
        """Get debugging tips for voice features"""
        return [
            "Use browser DevTools to monitor voice state changes",
            "Check Network tab for WebSocket connections and API calls",
            "Test with console.log in voice event handlers",
            "Use Chrome's chrome://webrtc-internals for detailed audio debugging",
            "Try the voice feature in different browsers to isolate issues",
            "Check if voice works in Cedar's demo/playground first",
            "Monitor the voice state with: const voice = useCedarStore(state => state.voice)"
        ]
    
    def _get_pattern_examples(self, component: str) -> Dict[str, str]:
        """Get pattern usage examples"""
        examples = {
            "basic": """
// Basic voice setup in your app
import { useCedarStore } from '@cedar/core';

function VoiceComponent() {
  const voice = useCedarStore(state => state.voice);
  
  // Use built-in toggle method
  const handleVoiceToggle = () => {
    voice.toggleVoice();
  };
  
  // Or control manually
  const startRecording = () => {
    if (!voice.isListening) {
      voice.startListening();
    }
  };
  
  const stopRecording = () => {
    if (voice.isListening) {
      voice.stopListening();
    }
  };
}
""",
            "VoiceIndicator": """
// Using VoiceIndicator from Cedar docs
import { VoiceIndicator } from '@cedar/voice';
import { useCedarStore } from '@cedar/core';

function MyVoiceApp() {
  const voice = useCedarStore((state) => state.voice);
  
  return (
    <div>
      {/* VoiceIndicator shows animated bars when listening */}
      <VoiceIndicator 
        voiceState={voice}
        className="absolute -top-12 right-0"
      />
      
      {/* ChatInput has voice built-in */}
      <ChatInput />
    </div>
  );
}
""",
            "permissions": """
// Handle voice permissions (from Cedar docs)
import { useCedarStore } from '@cedar/core';

function VoicePermissionHandler() {
  const voice = useCedarStore((state) => state.voice);
  
  // Check permission status
  const checkPermission = () => {
    switch (voice.voicePermissionStatus) {
      case 'granted':
        console.log('Microphone access granted');
        break;
      case 'denied':
        console.log('Microphone access denied');
        break;
      case 'not-supported':
        console.log('Voice not supported in this browser');
        break;
      default:
        // Request permission
        voice.requestMicrophonePermission();
    }
  };
  
  // Manual permission request
  const requestPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return 'granted';
    } catch (error) {
      if (error.name === 'NotAllowedError') {
        return 'denied';
      }
      throw error;
    }
  };
}
"""
        }
        
        return examples.get(component, examples["basic"])