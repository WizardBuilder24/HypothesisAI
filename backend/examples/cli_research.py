#!/usr/bin/env python3
"""
HypothesisAI CLI Research Interface
Command-line interface for running the multi-agent scientific research system.
"""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from agent.graph import graph
from agent.state import ResearchState
from agent.configuration import ResearchWorkflowConfiguration


console = Console()


class ResearchCLI:
    """Command-line interface for HypothesisAI research system."""
    
    def __init__(self):
        self.console = console
        self.graph = graph
        
    def display_welcome(self):
        """Display welcome banner."""
        welcome_text = """
# HypothesisAI Research System
        
**Multi-Agent Scientific Research Acceleration Platform**
        
5 Specialized Agents:
- 📚 Literature Hunter: Searches 125M+ papers
- 🔍 Knowledge Synthesizer: Identifies patterns
- 💡 Hypothesis Generator: Proposes novel directions
- 🔬 Methodology Designer: Suggests experiments
- ✅ Validation Agent: Cross-references claims
        """
        self.console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))
    
    def display_results(self, result: Dict[str, Any], verbose: bool = False):
        """Display research results in a formatted way."""
        
        # Display synthesized papers
        if result.get("papers"):
            self.console.print("\n[bold cyan]📚 Literature Review[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Title", style="cyan", width=50)
            table.add_column("Authors", width=30)
            table.add_column("Year", justify="center")
            table.add_column("Relevance", justify="center")
            
            for paper in result["papers"][:10]:  # Show top 10
                # Handle different data structures
                authors = paper.get("authors", [])
                if isinstance(authors, list):
                    authors_str = ", ".join(authors[:3])  # Show first 3 authors
                else:
                    authors_str = str(authors)
                
                table.add_row(
                    paper.get("title", "N/A")[:50],
                    authors_str[:30],
                    str(paper.get("year", "N/A")),
                    f"{paper.get('relevance_score', 0):.2f}"
                )
            self.console.print(table)
        
        # Display synthesis patterns
        synthesis = result.get("synthesis")
        if synthesis and synthesis.get("patterns"):
            self.console.print("\n[bold cyan]🔍 Knowledge Synthesis[/bold cyan]")
            for pattern in synthesis["patterns"]:
                self.console.print(Panel(
                    f"[yellow]Pattern:[/yellow] {pattern.get('description', 'N/A')}\n"
                    f"[green]Supporting Papers:[/green] {len(pattern.get('paper_ids', []))}\n"
                    f"[blue]Confidence:[/blue] {pattern.get('confidence', 0):.2f}",
                    border_style="green"
                ))
        
        # Display generated hypotheses
        if result.get("hypotheses"):
            self.console.print("\n[bold cyan]💡 Generated Hypotheses[/bold cyan]")
            for i, hypothesis in enumerate(result["hypotheses"], 1):
                self.console.print(Panel(
                    f"[bold]Hypothesis {i}:[/bold] {hypothesis.get('content', hypothesis.get('text', 'N/A'))}\n\n"
                    f"[yellow]Rationale:[/yellow] {hypothesis.get('rationale', hypothesis.get('reasoning', 'N/A'))}\n"
                    f"[green]Confidence:[/green] {hypothesis.get('confidence_score', 0):.2f}\n"
                    f"[blue]Novelty:[/blue] {hypothesis.get('novelty_score', 0):.2f}",
                    title=f"Hypothesis {i}",
                    border_style="cyan"
                ))
        
        # Display validation results
        if result.get("validation_results"):
            self.console.print("\n[bold cyan]✅ Validation Results[/bold cyan]")
            valid_count = result.get("valid_hypotheses_count", 0)
            total_count = len(result["validation_results"])
            self.console.print(Panel(
                f"[green]Valid Hypotheses:[/green] {valid_count}/{total_count}\n"
                f"[yellow]Average Confidence:[/yellow] {sum(v.get('confidence_score', 0) for v in result['validation_results'])/total_count:.2f}",
                title="Validation Summary",
                border_style="green"
            ))
        
        # Display final answer
        messages = result.get("messages", [])
        if messages:
            final_message = None
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content.strip():
                    final_message = msg
                    break
            
            if final_message:
                self.console.print("\n[bold cyan]📝 Final Research Summary[/bold cyan]")
                self.console.print(Panel(
                    final_message.content,
                    border_style="bold blue"
                ))

        # Verbose: display per-stage prompts/responses
        if verbose and result.get("stages"):
            self.console.print("\n[bold magenta]🔎 Agent Stages (prompt/response)[/bold magenta]")
            for stage in result.get("stages", []):
                agent = stage.get("agent")
                prompt = stage.get("prompt")
                response = stage.get("response")
                timestamp = stage.get("timestamp")
                panel_content = f"[bold]Agent:[/bold] {agent}\n[bold]Timestamp:[/bold] {timestamp}\n\n[bold]Prompt:[/bold]\n{prompt}\n\n[bold]Response:[/bold]\n{response}"
                self.console.print(Panel(panel_content, title=f"Stage: {agent}", border_style="magenta"))
    
    def save_results(self, result: Dict[str, Any], output_path: Optional[Path]):
        """Save research results to file."""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"research_results_{timestamp}.json")
        
        # Prepare serializable result
        serializable_result = {
            "timestamp": datetime.now().isoformat(),
            "papers": result.get("papers", []),
            "synthesis": result.get("synthesis", {}),
            "research_gaps": result.get("research_gaps", []),
            "hypotheses": result.get("hypotheses", []),
            "validation_results": result.get("validation_results", []),
            "valid_hypotheses_count": result.get("valid_hypotheses_count", 0),
            "workflow_complete": result.get("workflow_complete", False)
        }
        
        # Extract final summary from messages
        messages = result.get("messages", [])
        if messages:
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content.strip():
                    serializable_result["final_summary"] = msg.content
                    break
        
        with open(output_path, 'w') as f:
            json.dump(serializable_result, f, indent=2)
        
        self.console.print(f"\n[green]✅ Results saved to {output_path}[/green]")
    
    async def run_research(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run the research workflow."""
        # Initialize state
        state = {
            "messages": [HumanMessage(content=args.question)],
            "query": args.question,
            "workflow_id": None,
            "iteration": 0,
            "should_continue": True,
            "papers": [],
            "search_queries": [],
            "papers_found_count": 0,
            "synthesis": None,
            "patterns_found": [],
            "research_gaps": [],
            "hypotheses": [],
            "hypotheses_generated": 0,
            "validation_results": [],
            "valid_hypotheses_count": 0,
            "next_agent": None,
            "supervisor_reasoning": None,
            "search_completed": False,
            "synthesis_completed": False,
            "workflow_complete": False,
            "max_papers": args.literature_depth,
            "max_iterations": args.max_loops,
            "min_papers_threshold": 5,
            "num_hypotheses": args.hypothesis_count,
            "errors": [],
            "retry_counts": {},
            "started_at": None,
            "last_updated": None,
            "completed_at": None
        }
        
        # Configure the system
        config = ResearchWorkflowConfiguration(
            llm_provider="google",  # Can be made configurable
            llm_model=args.supervisor_model,
            max_papers=args.literature_depth,
            num_hypotheses=args.hypothesis_count,
            max_hypotheses_to_validate=args.hypothesis_count
        )
        
        # Run with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Running multi-agent research workflow...", total=None)
            
            # Execute the graph
            result = await self.graph.ainvoke(
                state,
                config=config.to_runnable_config()
            )
            
            progress.update(task, completed=True)
        
        return result


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="HypothesisAI - Multi-Agent Scientific Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What are the potential applications of quantum computing in drug discovery?"
  %(prog)s "How can CRISPR be used to treat genetic diseases?" --hypothesis-count 5
  %(prog)s "Latest advances in mRNA vaccine technology" --literature-depth 50 --output results.json
        """
    )
    
    # Required arguments
    parser.add_argument(
        "question",
        help="Research question or topic to investigate"
    )
    
    # Search configuration
    parser.add_argument(
        "--max-queries",
        type=int,
        default=5,
        help="Maximum number of search queries per agent (default: 5)"
    )
    parser.add_argument(
        "--literature-depth",
        type=int,
        default=5,
        help="Number of papers to analyze (default: 5)"
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=2,
        help="Maximum number of research iteration loops (default: 2)"
    )
    
    # Agent models configuration
    parser.add_argument(
        "--supervisor-model",
    default="gemini-2.0-flash-lite",
        help="Model for supervisor agent (default: gpt-4-turbo-preview)"
    )
    parser.add_argument(
        "--literature-model",
        default="gpt-4-turbo-preview",
        help="Model for literature search (default: gpt-4-turbo-preview)"
    )
    parser.add_argument(
        "--synthesis-model",
        default="claude-3-opus-20240229",
        help="Model for knowledge synthesis (default: claude-3-opus)"
    )
    parser.add_argument(
        "--hypothesis-model",
        default="claude-3-opus-20240229",
        help="Model for hypothesis generation (default: claude-3-opus)"
    )
    parser.add_argument(
        "--validation-model",
        default="gpt-4-turbo-preview",
        help="Model for validation (default: gpt-4-turbo-preview)"
    )
    
    # Output configuration
    parser.add_argument(
        "--hypothesis-count",
        type=int,
        default=2,
        help="Number of hypotheses to generate (default: 2)"
    )
    parser.add_argument(
        "--experimental-validation",
        action="store_true",
        help="Include experimental validation suggestions"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path for results (JSON format)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output, only show final results"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed agent interactions"
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = ResearchCLI()

    if not args.quiet:
        cli.display_welcome()
        cli.console.print(f"\n[bold]Research Question:[/bold] {args.question}\n")
    
    try:
        # Run research
        result = asyncio.run(cli.run_research(args))
        
        # Display results
        if not args.quiet:
            cli.display_results(result, verbose=args.verbose)
        
        # Save results if requested
        if args.output:
            cli.save_results(result, args.output)
        
        # In quiet mode, just print the final answer
        if args.quiet:
            messages = result.get("messages", [])
            if messages:
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and msg.content.strip():
                        print(msg.content)
                        break
                
    except KeyboardInterrupt:
        cli.console.print("\n[yellow]Research interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        cli.console.print(f"\n[red]Error: {e}[/red]")
        if args.verbose:
            import traceback
            cli.console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()