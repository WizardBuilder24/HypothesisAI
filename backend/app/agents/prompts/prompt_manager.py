"""
Prompt Manager for loading and managing YAML-based prompts
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from dataclasses import dataclass
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@dataclass
class Prompt:
    """Prompt data structure"""
    template: str
    variables: List[str]
    settings: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    
    def format(self, **kwargs) -> str:
        """
        Format the prompt with provided variables
        
        Args:
            **kwargs: Variables to substitute in template
            
        Returns:
            Formatted prompt string
            
        Raises:
            KeyError: If required variable is missing
        """
        # Check all required variables are provided
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise KeyError(f"Missing required variables: {missing}")
        
        # Format the template
        return self.template.format(**kwargs)
    
    def format_safe(self, **kwargs) -> str:
        """
        Format prompt with safe fallbacks for missing variables
        
        Args:
            **kwargs: Variables to substitute in template
            
        Returns:
            Formatted prompt string with placeholders for missing vars
        """
        # Create safe dict with placeholders for missing values
        safe_kwargs = {var: kwargs.get(var, f"<{var}>") for var in self.variables}
        safe_kwargs.update({k: v for k, v in kwargs.items() if k not in self.variables})
        
        return self.template.format(**safe_kwargs)


class PromptManager:
    """
    Manages prompt loading and caching from YAML files
    """
    
    def __init__(self, prompt_dir: Optional[Path] = None):
        """
        Initialize PromptManager
        
        Args:
            prompt_dir: Directory containing prompt YAML files
        """
        if prompt_dir is None:
            # Default to app/agents/prompts/
            prompt_dir = Path(__file__).parent
        
        self.prompt_dir = Path(prompt_dir)
        self.prompts: Dict[str, Any] = {}
        self.system_prompts: Dict[str, str] = {}
        self.domain_configs: Dict[str, Any] = {}
        
        # Load prompts on initialization
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompts from YAML files"""
        yaml_files = self.prompt_dir.glob("*.yaml")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                    # Load prompts
                    if 'prompts' in data:
                        self._parse_prompts(data['prompts'])
                    
                    # Load system prompts
                    if 'system_prompts' in data:
                        self.system_prompts.update(data['system_prompts'])
                    
                    # Load domain configs
                    if 'domain_configs' in data:
                        self.domain_configs.update(data['domain_configs'])
                    
                    logger.info(f"Loaded prompts from {yaml_file.name}")
                    
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
    
    def _parse_prompts(self, prompts_data: Dict[str, Any]) -> None:
        """Parse prompts from YAML data structure"""
        for agent_name, agent_prompts in prompts_data.items():
            if agent_name not in self.prompts:
                self.prompts[agent_name] = {}
            
            for prompt_name, prompt_data in agent_prompts.items():
                prompt = Prompt(
                    template=prompt_data['template'],
                    variables=prompt_data.get('variables', []),
                    settings=prompt_data.get('settings'),
                    examples=prompt_data.get('examples')
                )
                self.prompts[agent_name][prompt_name] = prompt
    
    @lru_cache(maxsize=128)
    def get_prompt(self, agent: str, prompt_name: str = 'default') -> Prompt:
        """
        Get a specific prompt
        
        Args:
            agent: Agent name (e.g., 'literature_hunter')
            prompt_name: Specific prompt name (e.g., 'search')
            
        Returns:
            Prompt object
            
        Raises:
            KeyError: If prompt not found
        """
        if agent not in self.prompts:
            raise KeyError(f"No prompts found for agent: {agent}")
        
        # Try to get specific prompt, fall back to 'default' if exists
        if prompt_name not in self.prompts[agent]:
            if 'default' in self.prompts[agent]:
                prompt_name = 'default'
            else:
                raise KeyError(f"Prompt '{prompt_name}' not found for agent '{agent}'")
        
        return self.prompts[agent][prompt_name]
    
    def get_system_prompt(self, mode: str = 'default') -> str:
        """
        Get system prompt for a specific mode
        
        Args:
            mode: System mode (e.g., 'creative_mode', 'rigorous_mode')
            
        Returns:
            System prompt string
        """
        # Handle nested structure for system prompts
        if 'research_assistant' in self.system_prompts:
            if mode in self.system_prompts['research_assistant']:
                return self.system_prompts['research_assistant'][mode]
        
        if mode in self.system_prompts:
            return self.system_prompts[mode]
        
        # Default fallback
        return "You are a helpful research assistant."
    
    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """
        Get configuration for a specific research domain
        
        Args:
            domain: Domain name (e.g., 'biomedical', 'machine_learning')
            
        Returns:
            Domain configuration dictionary
        """
        return self.domain_configs.get(domain, {})
    
    def format_prompt(self, agent: str, prompt_name: str = 'default', **kwargs) -> str:
        """
        Get and format a prompt in one call
        
        Args:
            agent: Agent name
            prompt_name: Prompt name
            **kwargs: Variables to format the prompt with
            
        Returns:
            Formatted prompt string
        """
        prompt = self.get_prompt(agent, prompt_name)
        return prompt.format(**kwargs)
    
    def reload_prompts(self) -> None:
        """Reload all prompts from disk (useful for development)"""
        self.prompts.clear()
        self.system_prompts.clear()
        self.domain_configs.clear()
        self.get_prompt.cache_clear()  # Clear LRU cache
        self._load_prompts()
        logger.info("Prompts reloaded")
    
    def list_prompts(self, agent: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List available prompts
        
        Args:
            agent: Optional agent name to filter by
            
        Returns:
            Dictionary of agent names to prompt names
        """
        if agent:
            return {agent: list(self.prompts.get(agent, {}).keys())}
        return {ag: list(prompts.keys()) for ag, prompts in self.prompts.items()}


# Singleton instance for easy importing
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get or create the singleton PromptManager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager