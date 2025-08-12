from typing import List, Dict, Any, Optional
import re

from .docs import DocsIndex


class VoiceSpecialistService:
    """Service for voice-specific Cedar-OS development assistance"""
    
    # Voice component mappings (from Cedar docs)
    VOICE_COMPONENTS = {
        "VoiceIndicator": {
            "description": "Visual feedback component with smooth animations powered by Motion for React",
            "props": ["voiceState", "className"],
            "voiceState_fields": ["isListening", "isSpeaking", "transcription", "currentUtterance"],
            "imports": "import { VoiceIndicator } from '@cedar/voice';"
        },
        "VoiceButton": {
            "description": "Microphone toggle button with visual states and automatic permission handling",
            "props": ["size", "variant", "className"],
            "sizes": ["small", "medium", "large"],
            "variants": ["primary", "secondary", "outline"],
            "visual_states": ["red pulsing (recording)", "green (playing)", "gray (disabled)"]
        },
        "VoiceSettings": {
            "description": "Comprehensive voice configuration panel",
            "settings": {
                "language": "Speech recognition/synthesis language (required)",
                "voiceId": "Voice model: alloy, echo, fable, onyx, nova, shimmer",
                "rate": "Speech rate (0.25-4.0, default: 1)",
                "volume": "Volume level (0-1, default: 1)",
                "autoAddToMessages": "Auto-add transcriptions to chat",
                "useBrowserTTS": "Use browser TTS instead of OpenAI"
            }
        },
        "VoiceStatusPanel": {
            "description": "Comprehensive status panel showing all voice information",
            "displays": ["permission status", "connection state", "current activity", "error messages"],
            "permission_states": ["granted", "denied", "not-supported", "prompt"],
            "imports": "import { VoiceStatusPanel } from './VoiceComponents';"
        },
        "VoiceWaveform": {
            "description": "Audio waveform visualizer for real-time voice",
            "props": ["className", "height", "color"],
            "imports": "import { VoiceWaveform } from './VoiceComponents';"
        }
    }
    
    # Voice implementation templates
    VOICE_TEMPLATES = {
        "next_app_router": """
'use client';

import { ChatInput } from 'cedar-os-components';
import { VoiceIndicator } from '@cedar/voice';
import { useCedarStore } from '@cedar/core';

export default function VoiceChat() {
  const voice = useCedarStore((state) => state.voice);
  
  return (
    <div className="relative">
      <ChatInput 
        stream={true}
        className="w-full"
        // Voice features are built-in to ChatInput
      />
      {voice.isListening && (
        <VoiceIndicator 
          voiceState={voice}
          className="absolute -top-12 right-0"
        />
      )}
    </div>
  );
}
""",
        "react_basic": """
import React from 'react';
import { ChatInput } from 'cedar-os-components';
import { useCedarStore } from '@cedar/core';

function VoiceInterface() {
  const voice = useCedarStore((state) => state.voice);
  
  // ChatInput handles voice toggle automatically
  // but you can also control it manually:
  const handleVoiceToggle = () => {
    voice.toggleVoice(); // Built-in toggle method
  };
  
  return (
    <div>
      <ChatInput 
        // Voice button and M key shortcut work automatically
      />
      <div className="mt-2 text-sm">
        Status: {voice.isListening ? 'Recording...' : 'Ready'}
        {voice.voiceError && (
          <div className="text-red-500">{voice.voiceError}</div>
        )}
      </div>
    </div>
  );
}
""",
        "custom_voice_button": """
import { Mic, MicOff } from 'lucide-react';
import { useCedarStore } from '@cedar/core';

export function CustomVoiceButton() {
  const voice = useCedarStore((state) => state.voice);
  
  const handleClick = async () => {
    if (!voice.voicePermissionStatus || voice.voicePermissionStatus === 'prompt') {
      await voice.requestMicrophonePermission();
    }
    
    if (voice.isListening) {
      voice.stopListening();
    } else {
      voice.startListening();
    }
  };
  
  return (
    <button
      onClick={handleClick}
      className={`p-3 rounded-full transition-all ${
        voice.isListening 
          ? 'bg-red-500 text-white animate-pulse' 
          : 'bg-gray-200 hover:bg-gray-300'
      }`}
      disabled={voice.voicePermissionStatus === 'denied'}
    >
      {voice.isListening ? <MicOff /> : <Mic />}
    </button>
  );
}
"""
    }
    
    def __init__(self, docs_index: Optional[DocsIndex] = None):
        self.docs_index = docs_index
    
    def get_voice_component_info(self, component: str) -> Dict[str, Any]:
        """Get detailed information about a voice component"""
        return self.VOICE_COMPONENTS.get(component, {
            "description": "Voice component for Cedar-OS",
            "props": [],
            "events": []
        })
    
    def get_voice_template(self, framework: str, component: str = "basic") -> str:
        """Get implementation template for voice features"""
        template_key = f"{framework}_{component}" if component != "basic" else framework
        
        # Map framework to template key
        template_map = {
            "nextjs": "next_app_router",
            "react": "react_basic",
            "custom": "custom_voice_button"
        }
        
        key = template_map.get(framework, "react_basic")
        return self.VOICE_TEMPLATES.get(key, self.VOICE_TEMPLATES["react_basic"])
    
    def analyze_voice_code(self, code: str) -> Dict[str, Any]:
        """Analyze code for voice-related issues and improvements"""
        analysis = {
            "has_voice_imports": False,
            "has_voice_state": False,
            "has_permission_handling": False,
            "has_error_handling": False,
            "issues": [],
            "suggestions": []
        }
        
        # Check for voice imports
        if "useCedarStore" in code or "VoiceIndicator" in code or "ChatInput" in code:
            analysis["has_voice_imports"] = True
        else:
            analysis["issues"].append("Missing Cedar voice component imports")
            analysis["suggestions"].append("Import voice components from 'cedar-os-components'")
        
        # Check for voice state usage
        if "voice" in code and ("useCedarStore" in code or "state.voice" in code):
            analysis["has_voice_state"] = True
        else:
            analysis["issues"].append("Not using voice state from Cedar store")
            analysis["suggestions"].append("Use: const voice = useCedarStore(state => state.voice)")
        
        # Check for permission handling
        if "permission" in code.lower() or "getUserMedia" in code:
            analysis["has_permission_handling"] = True
        else:
            analysis["suggestions"].append("Consider adding microphone permission handling")
        
        # Check for error handling
        if "try" in code and "catch" in code and "voice" in code:
            analysis["has_error_handling"] = True
        else:
            analysis["suggestions"].append("Add error handling for voice operations")
        
        # Check for common issues
        if "http://" in code and "voice" in code:
            analysis["issues"].append("Voice features require HTTPS in production")
        
        if "startListening()" in code and "stopListening()" not in code:
            analysis["suggestions"].append("Add stopListening() to properly cleanup voice recording")
        
        return analysis
    
    def get_voice_configuration_guide(self) -> Dict[str, Any]:
        """Get comprehensive voice configuration guide"""
        return {
            "backend_requirements": {
                "openai_api": {
                    "required": True,
                    "env_var": "OPENAI_API_KEY",
                    "services": [
                        "Whisper API for transcription",
                        "TTS API for text-to-speech",
                        "Realtime API for WebRTC voice (optional)"
                    ]
                },
                "voice_endpoint": {
                    "required": False,
                    "description": "WebSocket endpoint for real-time voice streaming",
                    "default": "wss://api.openai.com/v1/realtime",
                    "custom": "Can be set via voice.setVoiceEndpoint()"
                }
            },
            "frontend_setup": {
                "permissions": [
                    "Request microphone access on first use",
                    "Handle permission denial gracefully",
                    "Show clear permission status in UI"
                ],
                "browser_apis": [
                    "navigator.mediaDevices.getUserMedia",
                    "MediaRecorder API",
                    "Web Audio API (optional)"
                ]
            },
            "state_management": {
                "voice_state_fields": [
                    "isListening - Boolean, true when recording audio",
                    "isSpeaking - Boolean, true when AI voice playing",
                    "transcription - String, current transcribed text",
                    "voicePermissionStatus - 'granted' | 'denied' | 'not-supported' | 'prompt'",
                    "voiceError - String | null, error messages",
                    "voiceSettings - VoiceSettings object",
                    "voiceEndpoint - String, WebSocket URL",
                    "currentUtterance - SpeechSynthesisUtterance | null"
                ]
            },
            "testing": {
                "checklist": [
                    "Test in HTTPS environment",
                    "Verify microphone permissions",
                    "Check audio playback",
                    "Test error scenarios",
                    "Verify state updates"
                ]
            }
        }
    
    def get_voice_troubleshooting_guide(self, error_type: str) -> Dict[str, Any]:
        """Get troubleshooting guide for specific voice errors"""
        guides = {
            "permission": {
                "causes": [
                    "User denied microphone access",
                    "Browser doesn't support getUserMedia",
                    "Not using HTTPS",
                    "Browser settings blocking mic"
                ],
                "solutions": [
                    "Check navigator.mediaDevices availability",
                    "Ensure HTTPS in production",
                    "Provide clear permission request UI",
                    "Guide users to browser settings"
                ],
                "code_example": """
// Check and request permissions
async function checkVoicePermissions() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error('Voice not supported in this browser');
  }
  
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
}
"""
            },
            "connection": {
                "causes": [
                    "WebSocket endpoint misconfigured",
                    "CORS issues with voice API",
                    "Network connectivity problems",
                    "Invalid API keys"
                ],
                "solutions": [
                    "Verify voice endpoint URL",
                    "Check API key configuration",
                    "Test WebSocket connection directly",
                    "Review CORS settings"
                ],
                "code_example": """
// Test voice endpoint connection
const testVoiceConnection = async () => {
  const ws = new WebSocket(process.env.NEXT_PUBLIC_VOICE_WS_URL);
  
  ws.onopen = () => console.log('Voice connection established');
  ws.onerror = (error) => console.error('Voice connection error:', error);
  ws.onclose = () => console.log('Voice connection closed');
  
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (ws.readyState === WebSocket.OPEN) {
        resolve(true);
      } else {
        reject(new Error('Connection timeout'));
      }
    }, 5000);
  });
};
"""
            },
            "audio": {
                "causes": [
                    "Browser autoplay policies",
                    "Audio context suspended",
                    "No audio output device",
                    "Volume muted"
                ],
                "solutions": [
                    "Require user interaction before audio",
                    "Resume AudioContext on user action",
                    "Check audio output devices",
                    "Provide volume controls"
                ],
                "code_example": """
// Handle audio playback with user interaction
const playVoiceResponse = async (audioUrl) => {
  const audio = new Audio(audioUrl);
  
  // Resume audio context if needed
  if (window.AudioContext) {
    const ctx = new AudioContext();
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }
  }
  
  try {
    await audio.play();
  } catch (error) {
    if (error.name === 'NotAllowedError') {
      // Need user interaction
      console.log('Click to enable audio playback');
    }
  }
};
"""
            }
        }
        
        return guides.get(error_type, {
            "causes": ["Unknown error type"],
            "solutions": ["Check browser console for details"],
            "code_example": "// Debug with: console.log(voice)"
        })
    
    def generate_voice_test_suite(self, component: str) -> str:
        """Generate test suite for voice components"""
        return f"""
import {{ render, screen, fireEvent, waitFor }} from '@testing-library/react';
import {{ {component} }} from './components';
import {{ useCedarStore }} from '@cedar/core';

// Mock Cedar store
jest.mock('@cedar/core', () => ({{
  useCedarStore: jest.fn()
}}));

describe('{component} Voice Component', () => {{
  const mockVoiceState = {{
    isListening: false,
    isSpeaking: false,
    transcription: '',
    voicePermissionStatus: 'granted',
    voiceError: null,
    voiceEndpoint: 'wss://api.openai.com/v1/realtime',
    toggleVoice: jest.fn(),
    startListening: jest.fn(),
    stopListening: jest.fn(),
    requestMicrophonePermission: jest.fn(),
    updateVoiceSettings: jest.fn()
  }};
  
  beforeEach(() => {{
    useCedarStore.mockReturnValue(mockVoiceState);
  }});
  
  test('renders voice component', () => {{
    render(<{component} />);
    // Add specific assertions for {component}
  }});
  
  test('handles voice toggle', async () => {{
    render(<{component} />);
    const voiceButton = screen.getByRole('button', {{ name: /mic/i }});
    
    fireEvent.click(voiceButton);
    await waitFor(() => {{
      expect(mockVoiceState.toggleVoice).toHaveBeenCalled();
    }});
  }});
  
  test('shows recording state', () => {{
    mockVoiceState.isListening = true;
    render(<{component} />);
    
    // Check for recording indicator
    expect(screen.getByText(/recording/i)).toBeInTheDocument();
  }});
  
  test('handles permission denial', () => {{
    mockVoiceState.voicePermissionStatus = 'denied';
    render(<{component} />);
    
    const voiceButton = screen.getByRole('button', {{ name: /mic/i }});
    expect(voiceButton).toBeDisabled();
  }});
}});
"""