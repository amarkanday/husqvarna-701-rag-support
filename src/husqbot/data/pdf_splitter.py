from pathlib import Path
import PyPDF2


def split_pdf(
    input_file: str,
    output_dir: str,
    pages_per_file: int = 10
) -> list[str]:
    """Split a PDF into smaller files.
    
    Args:
        input_file: Path to input PDF file
        output_dir: Directory to save split PDFs
        pages_per_file: Number of pages per output file
        
    Returns:
        List of paths to split PDF files
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get input file name without extension
    input_name = Path(input_file).stem
    
    # Open the PDF
    print(f"Opening {input_file}...")
    with open(input_file, 'rb') as file:
        # Create PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        print(f"Total pages: {total_pages}")
        
        # Calculate number of files needed
        num_files = (total_pages + pages_per_file - 1) // pages_per_file
        print(f"Splitting into {num_files} files...")
        
        output_files = []
        
        # Split the PDF
        for i in range(num_files):
            start_page = i * pages_per_file
            end_page = min((i + 1) * pages_per_file, total_pages)
            
            # Create PDF writer object
            pdf_writer = PyPDF2.PdfWriter()
            
            # Add pages to writer
            for page_num in range(start_page, end_page):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
            
            # Save the split PDF
            output_file = output_path / f"{input_name}_part{i+1:03d}.pdf"
            print(f"Writing pages {start_page+1}-{end_page} to {output_file}")
            
            with open(output_file, 'wb') as output:
                pdf_writer.write(output)
            
            output_files.append(str(output_file))
    
    print(f"Successfully split PDF into {len(output_files)} files")
    return output_files


if __name__ == "__main__":
    # Example usage
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    
    # Split owner's manual
    owners_pdf = data_dir / "raw" / "owners_manual" / "husky_om_701.pdf"
    owners_split_dir = data_dir / "raw" / "owners_manual" / "split"
    if owners_pdf.exists():
        split_pdf(str(owners_pdf), str(owners_split_dir))
    
    # Split repair manual
    repair_pdf = data_dir / "raw" / "repair_manual" / "husky_rm_701.pdf"
    repair_split_dir = data_dir / "raw" / "repair_manual" / "split"
    if repair_pdf.exists():
        split_pdf(str(repair_pdf), str(repair_split_dir)) 