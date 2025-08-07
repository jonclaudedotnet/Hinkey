#!/usr/bin/env python3
"""
Dolores Training Framework - System for practicing and improving podcast hosting skills
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from claude_dolores_bridge import ask_dolores, wait_for_dolores
from podcast_training_data_structure import PodcastTrainingDatabase, PodcastSkill
from podcast_conversation_flows import PodcastFlowDesigner, FlowState
import random

class DoloresTrainingFramework:
    """Framework for training Dolores in podcast hosting skills"""
    
    def __init__(self):
        self.training_db = PodcastTrainingDatabase()
        self.flow_designer = PodcastFlowDesigner()
        self.session_id = None
    
    def start_training_session(self, session_type: str = "skill_practice") -> str:
        """Start a new training session"""
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log session start
        conn = sqlite3.connect(self.training_db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO training_sessions 
            (session_id, session_type, session_date)
            VALUES (?, ?, ?)
        ''', (self.session_id, session_type, datetime.now()))
        conn.commit()
        conn.close()
        
        print(f"Started training session: {self.session_id}")
        return self.session_id
    
    def practice_conversation_flow(self, flow_id: str = "standard_interview"):
        """Practice a specific conversation flow with Dolores"""
        if not self.session_id:
            self.start_training_session("conversation_practice")
        
        flow = self.flow_designer.flows.get(flow_id)
        if not flow:
            print(f"Flow {flow_id} not found")
            return
        
        print(f"\\nPracticing conversation flow: {flow.name}")
        print(f"Duration: {flow.duration_minutes} minutes")
        print(f"States: {' -> '.join([state.value for state in flow.states])}")
        
        # Ask Dolores to practice this flow
        training_prompt = f'''
        Let's practice the "{flow.name}" conversation flow. Here's the structure:
        
        Flow States: {' -> '.join([state.value for state in flow.states])}
        Duration: {flow.duration_minutes} minutes
        
        Available prompts for each state:
        {json.dumps(flow.prompts_per_state, indent=2)}
        
        Practice running through this flow as if you're hosting a podcast. 
        Show me how you'd transition between states and use the prompts naturally.
        Remember your signature question timing!
        '''
        
        task_id = ask_dolores(
            "conversation_flow_practice",
            training_prompt,
            f"Training session: Practice {flow.name} conversation flow"
        )
        
        result = wait_for_dolores(task_id, timeout=45)
        if result:
            print("\\nDolores practiced the conversation flow:")
            print(result)
            self.log_practice_result(flow_id, result)
        else:
            print("No response from Dolores")
    
    def practice_specific_skill(self, skill_id: str):
        """Practice a specific podcast hosting skill"""
        if not self.session_id:
            self.start_training_session("skill_practice")
        
        # Get the skill from database
        skills = self.training_db.get_skills_by_mastery(1)
        skill = next((s for s in skills if s.skill_id == skill_id), None)
        
        if not skill:
            print(f"Skill {skill_id} not found")
            return
        
        print(f"\\nPracticing skill: {skill.name}")
        print(f"Current mastery level: {skill.mastery_level}/10")
        
        # Create practice scenarios
        practice_prompt = f'''
        Let's practice the skill: {skill.name}
        
        Description: {skill.description}
        
        Current examples:
        {json.dumps(skill.examples, indent=2)}
        
        Please demonstrate this skill by:
        1. Creating 3 new variations of this skill in action
        2. Showing how you'd use it in different podcast contexts
        3. Explaining what makes each example effective
        
        Focus on natural, conversational delivery that matches your personality.
        '''
        
        task_id = ask_dolores(
            "skill_practice",
            practice_prompt,
            f"Training session: Practice {skill.name} skill"
        )
        
        result = wait_for_dolores(task_id, timeout=30)
        if result:
            print("\\nDolores practiced the skill:")
            print(result)
            self.log_skill_practice(skill_id, result)
        else:
            print("No response from Dolores")
    
    def simulate_guest_interview(self, guest_type: str = "entrepreneur"):
        """Simulate a full interview with a virtual guest"""
        if not self.session_id:
            self.start_training_session("guest_interview")
        
        # Get appropriate flow for guest type
        flow = self.flow_designer.get_flow_by_guest_type(guest_type)
        
        simulation_prompt = f'''
        Let's simulate a full podcast interview! Here's the scenario:
        
        Guest Type: {guest_type}
        Conversation Flow: {flow.name}
        Duration: {flow.duration_minutes} minutes
        
        I want you to play both roles - the host (you, Dolores) AND create a realistic guest.
        
        Guest Profile:
        - Create a fictional but believable {guest_type}
        - Give them a background, expertise, and personality
        - Make them respond naturally to your questions
        
        Run through the entire interview flow:
        {' -> '.join([state.value for state in flow.states])}
        
        Show me how you'd:
        1. Open the conversation warmly
        2. Ask engaging follow-up questions
        3. Guide the conversation through each state
        4. Ask your signature question at the right moment
        5. Close gracefully
        
        Make it feel like a real podcast episode!
        '''
        
        task_id = ask_dolores(
            "interview_simulation",
            simulation_prompt,
            f"Training session: Simulate interview with {guest_type}"
        )
        
        result = wait_for_dolores(task_id, timeout=60)
        if result:
            print(f"\\nDolores simulated interview with {guest_type}:")
            print(result)
            self.log_interview_simulation(guest_type, result)
        else:
            print("No response from Dolores")
    
    def log_practice_result(self, flow_id: str, result: str):
        """Log the results of conversation flow practice"""
        # Simple scoring based on result length and content
        score = min(10.0, len(result) / 100)  # Basic scoring
        
        conn = sqlite3.connect(self.training_db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE training_sessions 
            SET skills_practiced = ?, performance_score = ?, feedback = ?
            WHERE session_id = ?
        ''', (json.dumps([flow_id]), score, result[:500], self.session_id))
        conn.commit()
        conn.close()
    
    def log_skill_practice(self, skill_id: str, result: str):
        """Log skill practice results and potentially update mastery"""
        # Update skill last practiced time
        conn = sqlite3.connect(self.training_db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE skills 
            SET last_practiced = ?
            WHERE skill_id = ?
        ''', (datetime.now(), skill_id))
        conn.commit()
        conn.close()
        
        print(f"Logged practice for skill: {skill_id}")
    
    def log_interview_simulation(self, guest_type: str, result: str):
        """Log interview simulation results"""
        score = min(10.0, len(result) / 150)  # Basic scoring
        
        conn = sqlite3.connect(self.training_db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE training_sessions 
            SET skills_practiced = ?, performance_score = ?, feedback = ?
            WHERE session_id = ?
        ''', (json.dumps([f"interview_{guest_type}"]), score, result[:500], self.session_id))
        conn.commit()
        conn.close()
    
    def get_recommended_training(self) -> Dict[str, any]:
        """Recommend what Dolores should practice next"""
        # Get skills that need practice (low mastery or not practiced recently)
        skills = self.training_db.get_skills_by_mastery(1)
        
        needs_practice = []
        for skill in skills:
            if skill.mastery_level < 7:  # Below expert level
                needs_practice.append(skill)
            elif skill.last_practiced is None:
                needs_practice.append(skill)
        
        recommendations = {
            "skills_to_practice": [s.skill_id for s in needs_practice[:3]],
            "recommended_flow": "standard_interview",
            "suggested_guest_types": ["entrepreneur", "artist", "philosopher"]
        }
        
        return recommendations

def main():
    """Demonstrate the training framework"""
    framework = DoloresTrainingFramework()
    
    print("Dolores Training Framework Initialized!")
    print("\\nAvailable training options:")
    print("1. Practice conversation flows")
    print("2. Practice specific skills")  
    print("3. Simulate guest interviews")
    
    # Get recommendations
    recommendations = framework.get_recommended_training()
    print(f"\\nRecommended training:")
    print(f"Skills to practice: {recommendations['skills_to_practice']}")
    print(f"Recommended flow: {recommendations['recommended_flow']}")
    
    # Example: Practice a skill
    if recommendations['skills_to_practice']:
        print(f"\\n=== Practicing skill: {recommendations['skills_to_practice'][0]} ===")
        framework.practice_specific_skill(recommendations['skills_to_practice'][0])

if __name__ == "__main__":
    main()