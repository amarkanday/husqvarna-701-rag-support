import click
import logging
from pathlib import Path
import time
from typing import List, Tuple


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_manual_parts(manual_type: str) -> List[Tuple[str, int]]:
    """Get all parts for a manual type."""
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    split_dir = data_dir / "raw" / f"{manual_type}_manual" / "split"
    parts = []
    
    # om = owner's manual, rm = repair manual
    prefix = "om" if manual_type == "owners" else "rm"
    pattern = f"husky_{prefix}_701_part*.pdf"
    logger.debug(f"Searching for pattern: {pattern} in {split_dir}")
    for file in sorted(split_dir.glob(pattern)):
        part_num = int(file.stem.split("part")[-1])
        parts.append((manual_type, part_num))
    
    logger.debug(f"Found {len(parts)} parts for {manual_type} manual")
    return parts


@click.command()
@click.option(
    '--project-id',
    envvar='GOOGLE_CLOUD_PROJECT',
    help='Google Cloud project ID',
    required=True
)
@click.option(
    '--location',
    default='us-central1',
    help='Google Cloud region'
)
@click.option(
    '--start-from-manual',
    type=click.Choice(['owners', 'repair']),
    default='owners',
    help='Which manual to start processing from'
)
@click.option(
    '--start-from-part',
    type=int,
    default=1,
    help='Which part number to start from'
)
@click.option(
    '--store-embeddings',
    is_flag=True,
    help='Generate and store embeddings'
)
def process_all(
    project_id: str,
    location: str,
    start_from_manual: str,
    start_from_part: int,
    store_embeddings: bool
):
    """Process all manual parts in sequence."""
    from husqbot.data.process_manuals import process_single_manual
    
    # Get all parts for both manuals
    all_parts = []
    if start_from_manual == 'owners':
        logger.debug("Getting owners manual parts")
        all_parts.extend(get_manual_parts('owners'))
    logger.debug("Getting repair manual parts")
    all_parts.extend(get_manual_parts('repair'))
    
    logger.debug(f"Total parts to process: {len(all_parts)}")
    
    # Filter based on start position
    started = False
    for manual_type, part_num in all_parts:
        if not started:
            if (manual_type == start_from_manual and
                    part_num >= start_from_part):
                started = True
                logger.debug(
                    f"Starting from {manual_type} manual part {part_num}"
                )
            else:
                logger.debug(
                    f"Skipping {manual_type} manual part {part_num}"
                )
                continue
                
        logger.info(f"Processing {manual_type} manual part {part_num}")
        try:
            # om = owner's manual, rm = repair manual
            prefix = "om" if manual_type == "owners" else "rm"
            file_name = (
                f"husky_{prefix}_701_part{part_num:03d}.pdf"
            )
            logger.debug(f"Processing file: {file_name}")
            process_single_manual(
                project_id=project_id,
                location=location,
                manual_type=manual_type,
                input_file=file_name,
                store_embeddings=store_embeddings
            )
            msg = (
                f"Successfully processed {manual_type} "
                f"manual part {part_num}"
            )
            logger.info(msg)
            # Small delay between parts to avoid rate limiting
            time.sleep(2)
        except Exception as e:
            msg = (
                f"Error processing {manual_type} manual "
                f"part {part_num}: {str(e)}"
            )
            logger.error(msg)
            raise


if __name__ == '__main__':
    process_all() 