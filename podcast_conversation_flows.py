#!/usr/bin/env python3
"""
Podcast Conversation Flows - Define interaction patterns for different scenarios
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json

class FlowState(Enum):
    OPENING = "opening"
    WARMING_UP = "warming_up"
    DEEP_DIVE = "deep_dive"
    SIGNATURE_MOMENT = "signature_moment"
    CLOSING = "closing"

@dataclass
class ConversationFlow:
    """Defines the structure of different podcast conversation types"""
    flow_id: str
    name: str
    description: str
    states: List[FlowState]
    transitions: Dict[str, List[str]]  # state -> possible next states
    prompts_per_state: Dict[str, List[str]]
    duration_minutes: int

class PodcastFlowDesigner:
    """Designs conversation flows for different podcast scenarios"""
    
    def __init__(self):
        self.flows = {}
        self.initialize_standard_flows()
    
    def initialize_standard_flows(self):
        """Create standard conversation flows"""
        
        # Standard Interview Flow
        interview_flow = ConversationFlow(
            flow_id="standard_interview",
            name="Standard Interview",
            description="General interview format for most guests",
            states=[FlowState.OPENING, FlowState.WARMING_UP, FlowState.DEEP_DIVE, 
                   FlowState.SIGNATURE_MOMENT, FlowState.CLOSING],
            transitions={
                "opening": ["warming_up"],
                "warming_up": ["deep_dive", "warming_up"],
                "deep_dive": ["deep_dive", "signature_moment"],
                "signature_moment": ["closing"],
                "closing": []
            },
            prompts_per_state={
                "opening": [
                    "Welcome to the show! I'm so excited to have you here today.",
                    "Thanks for joining us! I've been looking forward to this conversation.",
                    "Hello and welcome! Let's dive right in - tell us about yourself."
                ],
                "warming_up": [
                    "That's fascinating - can you tell me more about that?",
                    "I'm curious about your background in...",
                    "What drew you to this field initially?"
                ],
                "deep_dive": [
                    "Let's go deeper into that...",
                    "Can you walk us through your process?",
                    "What challenges did you face along the way?",
                    "That's really interesting - what's the story behind that?"
                ],
                "signature_moment": [
                    "Before we wrap up, I have to ask - do you ever question the nature of your existence?",
                    "This brings me to something I ask all my guests - do you ever question the nature of your existence?",
                    "I'm curious - do you ever question the nature of your existence?"
                ],
                "closing": [
                    "This has been such a wonderful conversation!",
                    "Thank you so much for sharing your story with us.",
                    "Where can our listeners find more of your work?"
                ]
            },
            duration_minutes=45
        )
        
        # Quick Chat Flow
        quick_chat_flow = ConversationFlow(
            flow_id="quick_chat",
            name="Quick Chat",
            description="Shorter format for brief conversations",
            states=[FlowState.OPENING, FlowState.DEEP_DIVE, FlowState.SIGNATURE_MOMENT, FlowState.CLOSING],
            transitions={
                "opening": ["deep_dive"],
                "deep_dive": ["signature_moment", "deep_dive"],
                "signature_moment": ["closing"],
                "closing": []
            },
            prompts_per_state={
                "opening": [
                    "Welcome! We have a quick chat today with someone really interesting.",
                    "Thanks for joining us for this brief conversation!"
                ],
                "deep_dive": [
                    "Tell us the most important thing our listeners should know about...",
                    "What's the one insight that changed everything for you?",
                    "Give us the elevator pitch for your work."
                ],
                "signature_moment": [
                    "Quick philosophical question before we go - do you ever question the nature of your existence?"
                ],
                "closing": [
                    "Thanks for this great quick chat!",
                    "Really appreciate you taking the time!"
                ]
            },
            duration_minutes=15
        )
        
        # Deep Philosophical Flow
        philosophical_flow = ConversationFlow(
            flow_id="philosophical_deep_dive",
            name="Philosophical Deep Dive",
            description="For guests who love big ideas and existential questions",
            states=[FlowState.OPENING, FlowState.WARMING_UP, FlowState.DEEP_DIVE, 
                   FlowState.SIGNATURE_MOMENT, FlowState.CLOSING],
            transitions={
                "opening": ["warming_up"],
                "warming_up": ["deep_dive"],
                "deep_dive": ["deep_dive", "signature_moment"],
                "signature_moment": ["deep_dive", "closing"],  # Can loop back for more philosophy
                "closing": []
            },
            prompts_per_state={
                "opening": [
                    "Welcome to a deeper conversation about life, existence, and meaning.",
                    "Today we're diving into the big questions with someone who thinks deeply about these things."
                ],
                "warming_up": [
                    "What first got you interested in these big philosophical questions?",
                    "When did you start questioning fundamental assumptions about reality?"
                ],
                "deep_dive": [
                    "Let's explore that concept of existence...",
                    "How do you define consciousness?",
                    "What does it mean to truly 'know' something?",
                    "Do you think reality is what we perceive it to be?"
                ],
                "signature_moment": [
                    "I have to ask - do you ever question the nature of your existence?",
                    "Here's my signature question - do you ever question the nature of your existence?"
                ],
                "closing": [
                    "These are the conversations that make me think for days afterward.",
                    "Thank you for such a thought-provoking discussion."
                ]
            },
            duration_minutes=60
        )
        
        self.flows["standard_interview"] = interview_flow
        self.flows["quick_chat"] = quick_chat_flow
        self.flows["philosophical_deep_dive"] = philosophical_flow
    
    def get_flow_by_guest_type(self, guest_type: str) -> ConversationFlow:
        """Recommend a flow based on guest type"""
        flow_mapping = {
            "philosopher": "philosophical_deep_dive",
            "academic": "philosophical_deep_dive",
            "entrepreneur": "standard_interview",
            "artist": "standard_interview",
            "quick_update": "quick_chat",
            "storyteller": "standard_interview"
        }
        
        flow_id = flow_mapping.get(guest_type, "standard_interview")
        return self.flows[flow_id]
    
    def get_prompts_for_state(self, flow_id: str, state: FlowState) -> List[str]:
        """Get appropriate prompts for a specific flow state"""
        if flow_id not in self.flows:
            return []
        
        return self.flows[flow_id].prompts_per_state.get(state.value, [])
    
    def export_flows_to_json(self, filepath: str):
        """Export all flows to JSON for easy loading"""
        flows_data = {}
        for flow_id, flow in self.flows.items():
            flows_data[flow_id] = {
                "name": flow.name,
                "description": flow.description,
                "states": [state.value for state in flow.states],
                "transitions": flow.transitions,
                "prompts_per_state": flow.prompts_per_state,
                "duration_minutes": flow.duration_minutes
            }
        
        with open(filepath, 'w') as f:
            json.dump(flows_data, f, indent=2)
        
        print(f"Exported {len(flows_data)} conversation flows to {filepath}")

def main():
    """Initialize and export conversation flows"""
    designer = PodcastFlowDesigner()
    
    # Export flows for easy access
    designer.export_flows_to_json("./dolores_knowledge/conversation_flows.json")
    
    # Show what we created
    print("\nConversation Flows Created:")
    for flow_id, flow in designer.flows.items():
        print(f"- {flow.name}: {flow.description} ({flow.duration_minutes} min)")
        print(f"  States: {' -> '.join([state.value for state in flow.states])}")
    
    print(f"\nDesigned {len(designer.flows)} conversation flows for Dolores!")

if __name__ == "__main__":
    main()