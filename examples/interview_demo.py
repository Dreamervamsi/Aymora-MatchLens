import asyncio
import sys
from matchlens.interview import InterviewOrchestrator, InterviewStatus


async def run_cli_interview_demo():
    """
    Interactive CLI demo demonstrating a multi-turn onboarding interview with MatchLens.
    Run with GROQ_API_KEY set in environment or with mocked client.
    """
    print("\n=======================================================")
    print("      MatchLens AI Conversational Onboarding Demo      ")
    print("=======================================================\n")

    orchestrator = InterviewOrchestrator()
    user_id = "demo_user_42"
    session_id = "demo_session_001"

    state, opening_msg = orchestrator.start_interview(user_id=user_id, session_id=session_id)
    print(f"Assistant: {opening_msg}\n")

    while True:
        try:
            user_input = input("User: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting interview demo.")
            break

        if not user_input:
            continue

        turn_result = await orchestrator.process_turn(session_id=session_id, user_message=user_input)

        print(f"\n[Status: {turn_result.interview_status.value} | Topic: {turn_result.current_topic.value} | Progress: {turn_result.progress.percentage}%]")
        if turn_result.newly_extracted_fields:
            print(f"  -> Newly Extracted: {', '.join(turn_result.newly_extracted_fields)}")
        if turn_result.pending_confirmations:
            print(f"  -> Pending Confirmations: {[p.field_name for p in turn_result.pending_confirmations]}")

        print(f"\nAssistant: {turn_result.assistant_message}\n")

        if turn_result.is_ready_for_review:
            print("=======================================================")
            print("         Profile Interview Ready for Review!           ")
            print("=======================================================")
            draft_profile = orchestrator.get_draft_profile(session_id)
            print(f"User ID: {draft_profile.user_id}")
            print(f"Confirmed Attributes: {draft_profile.attributes.model_dump(exclude_none=True)}")
            print(f"Partner Expectations: {draft_profile.expectations.model_dump(exclude_none=True)}")
            
            confirm = input("\nConfirm and finalize profile? (yes/no): ").strip().lower()
            if confirm in ("yes", "y"):
                final_profile = orchestrator.confirm_draft_profile(session_id)
                print("\nProfile successfully finalized and status set to COMPLETED!")
            else:
                print("\nProfile left in READY_FOR_REVIEW state.")
            break


if __name__ == "__main__":
    asyncio.run(run_cli_interview_demo())
