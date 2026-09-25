import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BucketChip } from "@/components/ui";

describe("BucketChip", () => {
  it("shows the default label for each bucket", () => {
    render(<BucketChip variant="well" />);
    expect(screen.getByText("Performing well")).toBeInTheDocument();
  });

  it("lets the label be overridden, e.g. to include a count", () => {
    render(<BucketChip variant="under">Underperforming (9)</BucketChip>);
    expect(screen.getByText("Underperforming (9)")).toBeInTheDocument();
  });
});
