"""
Integration tests for Router → Chat/Planner flow
Tests with timing, state tracking, and PDF report generation
"""
import asyncio
import time
import json
from typing import Dict, Any, List
from datetime import datetime
from app.agents.state import StoryState
from app.agents.conversation.router import router_agent
from app.agents.conversation.chat import chat_agent
from app.agents.workflow.graph import create_story_graph
from langchain_core.messages import HumanMessage


def create_base_state(**kwargs) -> StoryState:
    """Helper to create base state"""
    defaults = {
        "theme": "",
        "memory_summary": None,
        "intent": None,
        "chat_response": None,
        "language": "en",
        "story_outline": None,
        "needs_info": False,
        "missing_fields": None,
        "suggestions": None,
        "chapters": [],
        "completed_writers": [],
        "completed_image_gens": [],
        "finalized_text": None,
        "finalized_images": None,
        "session_id": "test-session",
        "messages": [],
    }
    defaults.update(kwargs)
    return defaults


class TestResult:
    """Test result with timing and state tracking"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.steps: List[Dict[str, Any]] = []
        self.final_state: Dict[str, Any] = {}
        self.total_time: float = 0.0
        self.passed: bool = False
        self.error: str = None
    
    def add_step(self, step_name: str, duration: float, input_data: Any, output_data: Any, state_before: Dict, state_after: Dict):
        """Add a test step with timing and state changes"""
        self.steps.append({
            "step": step_name,
            "duration": duration,
            "input": self._format_data(input_data),
            "output": self._format_data(output_data),
            "state_before": self._sanitize_state(state_before),
            "state_after": self._sanitize_state(state_after),
            "state_changes": self._get_state_changes(state_before, state_after)
        })
    
    def _format_data(self, data: Any) -> str:
        """Format data for display"""
        if data is None:
            return "None"
        if isinstance(data, dict):
            return json.dumps(data, indent=2, ensure_ascii=False)
        if isinstance(data, (list, tuple)):
            return json.dumps(data, indent=2, ensure_ascii=False)
        return str(data)
    
    def _sanitize_state(self, state: Dict) -> Dict:
        """Sanitize state for display"""
        sanitized = {}
        for key, value in state.items():
            if value is None:
                sanitized[key] = None
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "..."
            elif isinstance(value, (list, dict)):
                value_str = json.dumps(value, ensure_ascii=False)
                if len(value_str) > 500:
                    sanitized[key] = value_str[:500] + "..."
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        return sanitized
    
    def _get_state_changes(self, before: Dict, after: Dict) -> Dict:
        """Get state changes between before and after"""
        changes = {}
        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)
            if before_val != after_val:
                changes[key] = {
                    "before": str(before_val)[:200] if before_val is not None else None,
                    "after": str(after_val)[:200] if after_val is not None else None
                }
        return changes


def print_step_details(step_name: str, duration: float, input_data: Any, output_data: Any):
    """Print step details with full input/output"""
    print(f"\n{'='*80}")
    print(f"STEP: {step_name} (Duration: {duration:.3f}s)")
    print(f"{'='*80}")
    print(f"\n📥 INPUT:")
    print(f"{json.dumps(input_data, indent=2, ensure_ascii=False) if isinstance(input_data, dict) else input_data}")
    print(f"\n📤 OUTPUT:")
    print(f"{json.dumps(output_data, indent=2, ensure_ascii=False) if isinstance(output_data, dict) else output_data}")


async def test_1_chat_flow():
    """Test 1: Chat flow - Router → Chat"""
    print("\n" + "="*80)
    print("TEST 1: Chat Flow - Router → Chat")
    print("="*80)
    
    result = TestResult("Test 1: Chat Flow")
    start_time = time.time()
    
    try:
        # Initial state
        user_input = "Hello! How are you today?"
        state = create_base_state(theme=user_input)
        state_before = state.copy()
        
        print(f"\n📝 USER INPUT: {user_input}")
        
        # Step 1: Router Agent
        print_step_details("Router Agent", 0, {"theme": user_input, "memory_summary": state.get("memory_summary")}, None)
        step_start = time.time()
        router_result = await router_agent(state)
        step_duration = time.time() - step_start
        
        print_step_details("Router Agent", step_duration, {"theme": user_input}, router_result)
        
        state.update(router_result)
        state_after = state.copy()
        result.add_step("Router Agent", step_duration, {"theme": user_input}, router_result, state_before, state_after)
        
        # Verify intent
        if router_result.get("intent") != "chat":
            result.error = f"Expected intent 'chat', got '{router_result.get('intent')}'"
            result.passed = False
            return result
        
        # Step 2: Chat Agent
        print_step_details("Chat Agent", 0, {"theme": user_input, "memory_summary": state.get("memory_summary")}, None)
        step_start = time.time()
        chat_result = await chat_agent(state)
        step_duration = time.time() - step_start
        
        print_step_details("Chat Agent", step_duration, {"theme": user_input, "memory_summary": state.get("memory_summary")}, chat_result)
        
        state.update(chat_result)
        state_after = state.copy()
        result.add_step("Chat Agent", step_duration, {"theme": user_input}, chat_result, state_before, state_after)
        
        # Verify chat response
        if not chat_result.get("chat_response"):
            result.error = "Chat Agent did not return a response"
            result.passed = False
            return result
        
        result.passed = True
        result.final_state = state_after
        result.total_time = time.time() - start_time
        
        print(f"\n✅ Test 1 PASSED - Total time: {result.total_time:.3f}s")
        
    except Exception as e:
        result.error = str(e)
        result.passed = False
        result.total_time = time.time() - start_time
        print(f"\n❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    return result


async def test_2_story_generate_flow():
    """Test 2: Story generation flow - Router → Complete Story Graph"""
    print("\n" + "="*80)
    print("TEST 2: Story Generation Flow - Router → Complete Story Graph")
    print("="*80)
    
    result = TestResult("Test 2: Story Generation Flow")
    start_time = time.time()
    
    try:
        # Initial state
        user_input = "Create a story about a brave little dragon who learns to fly"
        state = create_base_state(theme=user_input)
        state_before = state.copy()
        
        print(f"\n📝 USER INPUT: {user_input}")
        
        # Step 1: Router Agent
        print_step_details("Router Agent", 0, {"theme": user_input}, None)
        step_start = time.time()
        router_result = await router_agent(state)
        step_duration = time.time() - step_start
        
        print_step_details("Router Agent", step_duration, {"theme": user_input}, router_result)
        
        state.update(router_result)
        state_after = state.copy()
        result.add_step("Router Agent", step_duration, {"theme": user_input}, router_result, state_before, state_after)
        
        # Verify intent
        if router_result.get("intent") != "story_generate":
            result.error = f"Expected intent 'story_generate', got '{router_result.get('intent')}'"
            result.passed = False
            return result
        
        # Step 2: Run Complete Story Graph
        print(f"\n{'='*80}")
        print("STEP: Complete Story Graph Execution")
        print(f"{'='*80}")
        print(f"\n📥 INPUT STATE:")
        print(json.dumps({k: v for k, v in state.items() if v is not None}, indent=2, ensure_ascii=False))
        
        graph = create_story_graph()
        config = {"configurable": {"thread_id": "test-thread-2"}}
        
        step_start = time.time()
        graph_steps = []
        final_state = state.copy()
        node_start_time = time.time()
        
        # Stream execution to capture each step
        async for event in graph.astream(state, config):
            for node_name, node_output in event.items():
                node_duration = time.time() - node_start_time
                
                # Update final_state with node output
                if isinstance(node_output, dict):
                    final_state.update(node_output)
                
                graph_steps.append({
                    "node": node_name,
                    "output": node_output,
                    "duration": node_duration
                })
                
                print(f"\n  Node: {node_name} (Duration: {node_duration:.3f}s)")
                print(f"  📥 Input to {node_name}:")
                print(json.dumps({k: v for k, v in final_state.items() if v is not None and k in ['theme', 'memory_summary', 'story_outline', 'chapters', 'completed_writers', 'completed_image_gens']}, indent=2, ensure_ascii=False)[:500] + "...")
                print(f"  📤 Output from {node_name}:")
                if isinstance(node_output, dict):
                    output_summary = {k: v for k, v in node_output.items() if v is not None}
                    print(json.dumps(output_summary, indent=2, ensure_ascii=False)[:500] + "...")
                else:
                    print(str(node_output)[:200] + "...")
                
                node_start_time = time.time()
        
        total_graph_duration = time.time() - step_start
        
        print(f"\n📤 OUTPUT STATE:")
        if final_state:
            print(json.dumps({k: v for k, v in final_state.items() if v is not None}, indent=2, ensure_ascii=False))
        
        result.add_step("Complete Story Graph", total_graph_duration, state, final_state, state_before, final_state or state)
        
        # Verify final state
        if not final_state:
            result.error = "Story Graph did not return final state"
            result.passed = False
            return result
        
        if not final_state.get("finalized_text") and not final_state.get("story_outline"):
            result.error = "Story Graph did not generate story outline or finalized text"
            result.passed = False
            return result
        
        result.passed = True
        result.final_state = final_state
        result.total_time = time.time() - start_time
        
        print(f"\n✅ Test 2 PASSED - Total time: {result.total_time:.3f}s")
        
    except Exception as e:
        result.error = str(e)
        result.passed = False
        result.total_time = time.time() - start_time
        print(f"\n❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    return result


async def test_3_multi_turn_conversation():
    """Test 3: Multi-turn conversation - Chat → Chat → Story Generate (Complete)"""
    print("\n" + "="*80)
    print("TEST 3: Multi-turn Conversation - Chat → Chat → Complete Story Generation")
    print("="*80)
    
    result = TestResult("Test 3: Multi-turn Conversation")
    start_time = time.time()
    state = create_base_state()
    
    try:
        # Turn 1: Chat
        print(f"\n{'='*80}")
        print("TURN 1: Chat Conversation")
        print(f"{'='*80}")
        user_input_1 = "Hello! How are you?"
        state["theme"] = user_input_1
        state_before = state.copy()
        
        print(f"\n📝 USER INPUT: {user_input_1}")
        
        step_start = time.time()
        router_result = await router_agent(state)
        router_duration = time.time() - step_start
        state.update(router_result)
        
        print_step_details("Router Agent", router_duration, {"theme": user_input_1}, router_result)
        
        if router_result.get("intent") == "chat":
            step_start = time.time()
            chat_result = await chat_agent(state)
            chat_duration = time.time() - step_start
            state.update(chat_result)
            
            print_step_details("Chat Agent", chat_duration, {"theme": user_input_1, "memory_summary": state.get("memory_summary")}, chat_result)
            
            result.add_step("Turn 1: Router → Chat", router_duration + chat_duration, 
                          {"theme": user_input_1}, {"router": router_result, "chat": chat_result}, 
                          state_before, state.copy())
        else:
            result.error = f"Turn 1: Expected 'chat' intent, got '{router_result.get('intent')}'"
            result.passed = False
            return result
        
        # Turn 2: Chat again
        print(f"\n{'='*80}")
        print("TURN 2: Chat Conversation Again")
        print(f"{'='*80}")
        user_input_2 = "What's your favorite color?"
        state["theme"] = user_input_2
        state_before = state.copy()
        memory_summary_before = state.get("memory_summary")
        
        print(f"\n📝 USER INPUT: {user_input_2}")
        print(f"📋 Memory Summary Before: {memory_summary_before}")
        
        step_start = time.time()
        router_result = await router_agent(state)
        router_duration = time.time() - step_start
        state.update(router_result)
        memory_summary_after = state.get("memory_summary")
        
        print_step_details("Router Agent", router_duration, {"theme": user_input_2, "memory_summary": memory_summary_before}, router_result)
        print(f"📋 Memory Summary After: {memory_summary_after}")
        print(f"✅ Memory Summary Updated: {memory_summary_before != memory_summary_after}")
        
        if router_result.get("intent") == "chat":
            step_start = time.time()
            chat_result = await chat_agent(state)
            chat_duration = time.time() - step_start
            state.update(chat_result)
            
            print_step_details("Chat Agent", chat_duration, {"theme": user_input_2, "memory_summary": memory_summary_after}, chat_result)
            
            result.add_step("Turn 2: Router → Chat", router_duration + chat_duration,
                          {"theme": user_input_2, "memory_summary": memory_summary_before}, 
                          {"router": router_result, "chat": chat_result},
                          state_before, state.copy())
        else:
            result.error = f"Turn 2: Expected 'chat' intent, got '{router_result.get('intent')}'"
            result.passed = False
            return result
        
        # Verify state persistence
        if not state.get("memory_summary"):
            result.error = "Memory summary not persisted after Turn 2"
            result.passed = False
            return result
        
        # Turn 3: Complete Story Generation
        print(f"\n{'='*80}")
        print("TURN 3: Complete Story Generation")
        print(f"{'='*80}")
        user_input_3 = "Now create a story about a magical forest with talking animals"
        state["theme"] = user_input_3
        state_before = state.copy()
        
        print(f"\n📝 USER INPUT: {user_input_3}")
        print(f"📋 Memory Summary: {state.get('memory_summary')}")
        
        step_start = time.time()
        router_result = await router_agent(state)
        router_duration = time.time() - step_start
        state.update(router_result)
        
        print_step_details("Router Agent", router_duration, {"theme": user_input_3, "memory_summary": state_before.get("memory_summary")}, router_result)
        
        if router_result.get("intent") == "story_generate":
            print(f"\n{'='*80}")
            print("STEP: Complete Story Graph Execution")
            print(f"{'='*80}")
            print(f"\n📥 INPUT STATE:")
            print(json.dumps({k: v for k, v in state.items() if v is not None}, indent=2, ensure_ascii=False))
            
            graph = create_story_graph()
            config = {"configurable": {"thread_id": "test-thread-3"}}
            
            step_start = time.time()
            graph_steps = []
            final_state = state.copy()
            node_start_time = time.time()
            
            async for event in graph.astream(state, config):
                for node_name, node_output in event.items():
                    node_duration = time.time() - node_start_time
                    
                    # Update final_state with node output
                    if isinstance(node_output, dict):
                        final_state.update(node_output)
                    
                    graph_steps.append({
                        "node": node_name,
                        "output": node_output,
                        "duration": node_duration
                    })
                    
                    print(f"\n  Node: {node_name} (Duration: {node_duration:.3f}s)")
                    print(f"  📥 Input to {node_name}:")
                    print(json.dumps({k: v for k, v in final_state.items() if v is not None and k in ['theme', 'memory_summary', 'story_outline', 'chapters', 'completed_writers', 'completed_image_gens']}, indent=2, ensure_ascii=False)[:500] + "...")
                    print(f"  📤 Output from {node_name}:")
                    if isinstance(node_output, dict):
                        output_summary = {k: v for k, v in node_output.items() if v is not None}
                        print(json.dumps(output_summary, indent=2, ensure_ascii=False)[:500] + "...")
                    else:
                        print(str(node_output)[:200] + "...")
                    
                    node_start_time = time.time()
            
            total_graph_duration = time.time() - step_start
            
            print(f"\n📤 OUTPUT STATE:")
            if final_state:
                print(json.dumps({k: v for k, v in final_state.items() if v is not None}, indent=2, ensure_ascii=False))
            
            result.add_step("Turn 3: Router → Complete Story Graph", router_duration + total_graph_duration,
                          {"theme": user_input_3, "memory_summary": state_before.get("memory_summary")},
                          {"router": router_result, "graph": final_state},
                          state_before, final_state or state)
        else:
            result.error = f"Turn 3: Expected 'story_generate' intent, got '{router_result.get('intent')}'"
            result.passed = False
            return result
        
        result.passed = True
        result.final_state = final_state or state
        result.total_time = time.time() - start_time
        
        print(f"\n✅ Test 3 PASSED - Total time: {result.total_time:.3f}s")
        
    except Exception as e:
        result.error = str(e)
        result.passed = False
        result.total_time = time.time() - start_time
        print(f"\n❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def generate_pdf_report(results: List[TestResult]):
    """Generate PDF report from test results"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
        from reportlab.lib.units import inch
        
        filename = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
        )
        story.append(Paragraph("Integration Test Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        total_time = sum(r.total_time for r in results)
        
        summary_data = [
            ['Total Tests', str(total_count)],
            ['Passed', str(passed_count)],
            ['Failed', str(total_count - passed_count)],
            ['Total Time', f"{total_time:.3f}s"],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed results for each test
        for result in results:
            story.append(PageBreak())
            
            # Test header
            status_color = "#00AA00" if result.passed else "#AA0000"
            status_text = "PASSED" if result.passed else "FAILED"
            
            story.append(Paragraph(f"<b>{result.test_name}</b>", styles['Heading1']))
            story.append(Paragraph(f"Status: <font color='{status_color}'> {status_text}</font>", styles['Normal']))
            story.append(Paragraph(f"Total Time: {result.total_time:.3f}s", styles['Normal']))
            
            if result.error:
                story.append(Paragraph(f"<font color='red'>Error: {result.error}</font>", styles['Normal']))
            
            story.append(Spacer(1, 0.2*inch))
            
            # Steps with full input/output
            for step in result.steps:
                story.append(Paragraph(f"<b>{step['step']}</b> (Duration: {step['duration']:.3f}s)", styles['Heading2']))
                
                # Input
                story.append(Paragraph("<b>Input:</b>", styles['Normal']))
                input_text = step.get('input', 'N/A')
                if len(input_text) > 1000:
                    input_text = input_text[:1000] + "..."
                story.append(Preformatted(input_text, styles['Code'], maxLineLength=80))
                story.append(Spacer(1, 0.1*inch))
                
                # Output
                story.append(Paragraph("<b>Output:</b>", styles['Normal']))
                output_text = step.get('output', 'N/A')
                if len(output_text) > 1000:
                    output_text = output_text[:1000] + "..."
                story.append(Preformatted(output_text, styles['Code'], maxLineLength=80))
                story.append(Spacer(1, 0.1*inch))
                
                # State changes
                if step.get('state_changes'):
                    story.append(Paragraph("<b>State Changes:</b>", styles['Normal']))
                    for key, change in list(step['state_changes'].items())[:10]:  # Limit to 10 changes
                        before = change['before'] or "None"
                        after = change['after'] or "None"
                        if len(before) > 100:
                            before = before[:100] + "..."
                        if len(after) > 100:
                            after = after[:100] + "..."
                        story.append(Paragraph(f"  {key}: {before} → {after}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Final state
            if result.final_state:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("<b>Final State:</b>", styles['Heading2']))
                final_state_str = json.dumps({k: v for k, v in result.final_state.items() if v is not None}, indent=2, ensure_ascii=False)
                if len(final_state_str) > 2000:
                    final_state_str = final_state_str[:2000] + "..."
                story.append(Preformatted(final_state_str, styles['Code'], maxLineLength=80))
        
        doc.build(story)
        print(f"\n📄 PDF Report generated: {filename}")
        return filename
    except ImportError:
        print("\n⚠️  reportlab not installed. Generating text report instead...")
        generate_text_report(results)
        return None
    except Exception as e:
        print(f"\n⚠️  PDF generation error: {e}. Generating text report instead...")
        generate_text_report(results)
        return None


def generate_text_report(results: List[TestResult]):
    """Generate text report if PDF generation fails"""
    filename = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Integration Test Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Summary
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        total_time = sum(r.total_time for r in results)
        
        f.write(f"Summary:\n")
        f.write(f"  Total Tests: {total_count}\n")
        f.write(f"  Passed: {passed_count}\n")
        f.write(f"  Failed: {total_count - passed_count}\n")
        f.write(f"  Total Time: {total_time:.3f}s\n\n")
        
        # Detailed results
        for result in results:
            f.write("="*80 + "\n")
            f.write(f"{result.test_name}\n")
            f.write(f"Status: {'PASSED' if result.passed else 'FAILED'}\n")
            f.write(f"Total Time: {result.total_time:.3f}s\n")
            if result.error:
                f.write(f"Error: {result.error}\n")
            f.write("\n")
            
            # Steps with full input/output
            for step in result.steps:
                f.write(f"Step: {step['step']} (Duration: {step['duration']:.3f}s)\n")
                f.write(f"  Input:\n{step.get('input', 'N/A')}\n")
                f.write(f"  Output:\n{step.get('output', 'N/A')}\n")
                if step.get('state_changes'):
                    f.write("  State Changes:\n")
                    for key, change in step['state_changes'].items():
                        f.write(f"    {key}: {change['before']} → {change['after']}\n")
                f.write("\n")
            
            # Final state
            if result.final_state:
                f.write("Final State:\n")
                f.write(json.dumps(result.final_state, indent=2, ensure_ascii=False))
                f.write("\n")
            f.write("\n")
    
    print(f"📄 Text Report generated: {filename}")


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("INTEGRATION TESTS - Router → Chat/Complete Story Graph Flow")
    print("="*80)
    
    results = []
    
    # Test 1: Chat flow
    result1 = await test_1_chat_flow()
    results.append(result1)
    
    # Test 2: Complete story generation flow
    result2 = await test_2_story_generate_flow()
    results.append(result2)
    
    # Test 3: Multi-turn conversation with complete story generation
    result3 = await test_3_multi_turn_conversation()
    results.append(result3)
    
    # Generate report
    print("\n" + "="*80)
    print("GENERATING REPORT...")
    print("="*80)
    
    generate_pdf_report(results)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    total_time = sum(r.total_time for r in results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Total Time: {total_time:.3f}s")
    
    for result in results:
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        print(f"\n{result.test_name}: {status} ({result.total_time:.3f}s)")
        if result.error:
            print(f"  Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
