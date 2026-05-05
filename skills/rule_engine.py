"""
Rule Engine Skill for Jitro Assistant
Allows users to define and execute custom rules using a safe, sandboxed approach
"""

import os
import json
import ast
import inspect
import textwrap
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class RuleEngineSkill:
    """A skill that allows creating and executing custom rules"""
    
    def __init__(self):
        self.name = "rule_engine"
        self.description = "Create and execute custom rules with Python-like syntax"
        self.version = "1.0.0"
        self.rules_file = "./custom_rules.json"
        self.load_rules()
    
    def load_rules(self):
        """Load saved rules from file"""
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
            except Exception as e:
                logger.error(f"Error loading rules: {e}")
                self.rules = {}
        else:
            self.rules = {}
    
    def save_rules(self):
        """Save rules to file"""
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
    
    def validate_rule_code(self, code: str) -> tuple[bool, str]:
        """
        Validate rule code for safety
        Returns (is_valid, error_message)
        """
        try:
            # Parse the code to check for syntax errors
            tree = ast.parse(code)
            
            # Check for dangerous constructs
            for node in ast.walk(tree):
                # Disallow imports (except specific safe ones)
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    # Allow only specific safe modules
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name not in ['math', 'random', 'datetime', 'json', 're']:
                                return False, f"Import '{alias.name}' is not allowed"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module not in ['math', 'random', 'datetime', 'json', 're']:
                            return False, f"Import from '{node.module}' is not allowed"
                
                # Disallow dangerous built-ins
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    dangerous_funcs = ['eval', 'exec', 'compile', 'open', '__import__', 
                                     'getattr', 'setattr', 'delattr', 'exit', 'quit']
                    if node.func.id in dangerous_funcs:
                        return False, f"Function '{node.func.id}' is not allowed"
                
                # Disallow attribute access to dangerous modules
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        dangerous_modules = ['os', 'sys', 'subprocess', 'shutil']
                        if node.value.id in dangerous_modules:
                            return False, f"Access to '{node.value.id}' module is not allowed"
            
            return True, "Code is valid"
            
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def execute_rule(self, rule_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a saved rule
        
        Args:
            rule_name: Name of the rule to execute
            context: Variables to make available in the rule execution
            
        Returns:
            Dictionary with execution results
        """
        if context is None:
            context = {}
        
        if rule_name not in self.rules:
            return {
                "success": False,
                "error": f"Rule '{rule_name}' not found",
                "available_rules": list(self.rules.keys())
            }
        
        rule_data = self.rules[rule_name]
        code = rule_data.get("code", "")
        
        # Validate code again before execution
        is_valid, error_msg = self.validate_rule_code(code)
        if not is_valid:
            return {
                "success": False,
                "error": f"Rule validation failed: {error_msg}",
                "rule_name": rule_name
            }
        
        try:
            # Prepare safe execution environment
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                },
                'math': __import__('math'),
                'random': __import__('random'),
                'datetime': __import__('datetime'),
                'json': __import__('json'),
                're': __import__('re'),
            }
            
            # Add context variables
            safe_globals.update(context)
            
            # Execute the code
            local_vars = {}
            exec(code, safe_globals, local_vars)
            
            # Extract result (look for 'result' variable or last expression)
            result = local_vars.get('result', None)
            if result is None and local_vars:
                # Get the last assigned variable
                result = list(local_vars.values())[-1] if local_vars else None
            
            return {
                "success": True,
                "rule_name": rule_name,
                "result": result,
                "local_variables": {k: v for k, v in local_vars.items() 
                                  if not k.startswith('_') and 
                                  not isinstance(v, (type, type(exec)))},
                "execution_time": rule_data.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Error executing rule {rule_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "rule_name": rule_name,
                "rule_code": code[:200] + "..." if len(code) > 200 else code
            }
    
    def create_rule(self, name: str, code: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new rule
        
        Args:
            name: Rule name (must be unique)
            code: Python code for the rule
            description: Optional description
            
        Returns:
            Dictionary with creation results
        """
        # Check if rule already exists
        if name in self.rules:
            return {
                "success": False,
                "error": f"Rule '{name}' already exists",
                "action": "Use update_rule to modify existing rule"
            }
        
        # Validate the code
        is_valid, error_msg = self.validate_rule_code(code)
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid rule code: {error_msg}",
                "rule_name": name
            }
        
        # Save the rule
        from datetime import datetime
        self.rules[name] = {
            "code": code,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.save_rules()
        
        return {
            "success": True,
            "rule_name": name,
            "message": f"Rule '{name}' created successfully",
            "rule": self.rules[name]
        }
    
    def update_rule(self, name: str, code: str = None, description: str = None) -> Dict[str, Any]:
        """
        Update an existing rule
        
        Args:
            name: Rule name to update
            code: New Python code (optional)
            description: New description (optional)
            
        Returns:
            Dictionary with update results
        """
        if name not in self.rules:
            return {
                "success": False,
                "error": f"Rule '{name}' not found",
                "available_rules": list(self.rules.keys())
            }
        
        # Validate code if provided
        if code is not None:
            is_valid, error_msg = self.validate_rule_code(code)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Invalid rule code: {error_msg}",
                    "rule_name": name
                }
            self.rules[name]["code"] = code
        
        # Update description if provided
        if description is not None:
            self.rules[name]["description"] = description
        
        # Update timestamp
        from datetime import datetime
        self.rules[name]["updated_at"] = datetime.now().isoformat()
        
        self.save_rules()
        
        return {
            "success": True,
            "rule_name": name,
            "message": f"Rule '{name}' updated successfully",
            "rule": self.rules[name]
        }
    
    def delete_rule(self, name: str) -> Dict[str, Any]:
        """
        Delete a rule
        
        Args:
            name: Rule name to delete
            
        Returns:
            Dictionary with deletion results
        """
        if name not in self.rules:
            return {
                "success": False,
                "error": f"Rule '{name}' not found",
                "available_rules": list(self.rules.keys())
            }
        
        deleted_rule = self.rules.pop(name)
        self.save_rules()
        
        return {
            "success": True,
            "rule_name": name,
            "message": f"Rule '{name}' deleted successfully",
            "deleted_rule": deleted_rule
        }
    
    def list_rules(self) -> Dict[str, Any]:
        """
        List all available rules
        
        Returns:
            Dictionary with rules list
        """
        rule_list = []
        for name, rule_data in self.rules.items():
            rule_list.append({
                "name": name,
                "description": rule_data.get("description", ""),
                "created_at": rule_data.get("created_at"),
                "updated_at": rule_data.get("updated_at"),
                "code_length": len(rule_data.get("code", ""))
            })
        
        return {
            "success": True,
            "rules": rule_list,
            "count": len(rule_list)
        }
    
    def get_rule(self, name: str) -> Dict[str, Any]:
        """
        Get a specific rule
        
        Args:
            name: Rule name
            
        Returns:
            Dictionary with rule details
        """
        if name not in self.rules:
            return {
                "success": False,
                "error": f"Rule '{name}' not found",
                "available_rules": list(self.rules.keys())
            }
        
        return {
            "success": True,
            "rule_name": name,
            "rule": self.rules[name]
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execute method for the skill interface
        
        Args:
            parameters: Dictionary containing:
                - action: "create", "update", "delete", "list", "get", "execute"
                - rule_name: Name of the rule (for most actions)
                - code: Python code (for create/update)
                - description: Rule description (optional)
                - context: Variables for rule execution (for execute action)
                
        Returns:
            Dictionary with action results
        """
        action = parameters.get("action", "list")
        rule_name = parameters.get("rule_name", "")
        
        if action == "create":
            code = parameters.get("code", "")
            description = parameters.get("description", "")
            return self.create_rule(rule_name, code, description)
        
        elif action == "update":
            code = parameters.get("code")
            description = parameters.get("description")
            return self.update_rule(rule_name, code, description)
        
        elif action == "delete":
            return self.delete_rule(rule_name)
        
        elif action == "list":
            return self.list_rules()
        
        elif action == "get":
            return self.get_rule(rule_name)
        
        elif action == "execute":
            context = parameters.get("context", {})
            return self.execute_rule(rule_name, context)
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": ["create", "update", "delete", "list", "get", "execute"]
            }

# For dynamic loading
def get_skill():
    """Factory function to get skill instance"""
    return RuleEngineSkill()