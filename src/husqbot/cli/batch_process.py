import click
from pathlib import Path
import subprocess
import time


def process_manual_parts(
    manual_type: str,
    project_id: str,
    start_part: int = 1
):
    """Process all parts of a manual sequentially.
    
    Args:
        manual_type: Type of manual (owners/repair)
        project_id: Google Cloud project ID
        start_part: Part number to start from
    """
    # Get the split directory
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    split_dir = data_dir / "raw" / f"{manual_type}_manual" / "split"
    
    # Get all parts
    parts = sorted(split_dir.glob("*_part*.pdf"))
    if not parts:
        print("No parts found for", manual_type, "manual")
        return
    
    total_parts = len(parts)
    print(f"Found {total_parts} parts for {manual_type} manual")
    
    # Process each part
    for part_num in range(start_part, total_parts + 1):
        msg = f"\nProcessing {manual_type} manual part {part_num}"
        print(f"{msg} of {total_parts}")
        
        try:
            # Run the process-part command
            cmd = [
                "python", "-m", "husqbot.cli.main",
                "process-part",
                "--project-id", project_id,
                "--manual-type", manual_type,
                "--part-number", str(part_num)
            ]
            
            subprocess.run(cmd, check=True)
            print(f"Successfully processed part {part_num}")
            
            # Add a small delay between parts
            time.sleep(2)
            
        except subprocess.CalledProcessError as e:
            print(f"Error processing part {part_num}: {e}")
            print("Stopping processing")
            break
        except Exception as e:
            print(f"Unexpected error processing part {part_num}: {e}")
            print("Stopping processing")
            break


@click.command()
@click.option(
    '--project-id',
    required=True,
    help='Google Cloud project ID'
)
@click.option(
    '--manual-type',
    type=click.Choice(['owners', 'repair']),
    required=True,
    help='Type of manual to process'
)
@click.option(
    '--start-part',
    type=int,
    default=1,
    help='Part number to start from'
)
def main(project_id: str, manual_type: str, start_part: int):
    """Process all parts of a manual."""
    process_manual_parts(manual_type, project_id, start_part)


if __name__ == '__main__':
    main() 