from pathlib import Path
from .terraform_fmt import terraform_fmt
from .heredoc_fmt import convert_to_indented_heredoc, align_heredoc_closing_delimited
from .custom_fmt import reorder_resource_properties, align_key_value_pairs


def main():
    print("Begin formatting...")
    input_folder = Path("unformatted")
    output_folder = Path("formatted")
    output_folder.mkdir(exist_ok=True)

    for tf_file in input_folder.glob("*.tf"):
        print(f"Formatting: {tf_file.name}")

        original_unformatted_content = tf_file.read_text(encoding="utf-8")
        
        reorder_resource_properties_output_content = reorder_resource_properties(original_unformatted_content)
        reorder_resource_properties_output_file = output_folder / f"reorder_resource_properties-{tf_file.name}"
        reorder_resource_properties_output_file.write_text(reorder_resource_properties_output_content, encoding="utf-8")
        print(f"✔ Reordered the resource properties -> {reorder_resource_properties_output_file}")
        
        reorder_resource_properties_file_content = reorder_resource_properties_output_file.read_text(encoding="utf-8")
        
        indented_heredoc_output_content = convert_to_indented_heredoc(reorder_resource_properties_file_content)
        indented_heredoc_output_file = output_folder / f"indented-heredoc-{tf_file.name}"
        indented_heredoc_output_file.write_text(indented_heredoc_output_content, encoding="utf-8")
        print(f"✔ Converted to indented heredoc -> {indented_heredoc_output_file}")
        
        indented_heredoc_file_content = indented_heredoc_output_file.read_text(encoding="utf-8")
        
        aligned_heredoc_output_content = align_heredoc_closing_delimited(indented_heredoc_file_content)
        aligned_heredoc_output_file = output_folder / f"aligned-heredoc-{tf_file.name}"
        aligned_heredoc_output_file.write_text(aligned_heredoc_output_content, encoding="utf-8")
        print(f"✔ Modified to align heredoc closing delimited -> {aligned_heredoc_output_file}")
        
        aligned_heredoc_file_content = aligned_heredoc_output_file.read_text(encoding="utf-8")
        
        tf_fmt_formatted_output_content = terraform_fmt(aligned_heredoc_file_content)
        tf_fmt_output_file = output_folder / f"formatted-official-{tf_file.name}"
        tf_fmt_output_file.write_text(tf_fmt_formatted_output_content, encoding="utf-8")
        print(f"✔ Formatted file by `terraform fmt` -> {tf_fmt_output_file}")
        
        align_key_value_pairs_output_content = align_key_value_pairs(aligned_heredoc_file_content)
        align_key_value_pairs_output_file = output_folder / f"formatted-custom-{tf_file.name}"
        align_key_value_pairs_output_file.write_text(align_key_value_pairs_output_content, encoding="utf-8")
        print(f"✔ Formatted file by aligning = in key-value pairs -> {align_key_value_pairs_output_file}")  

if __name__ == "__main__":
    main()
