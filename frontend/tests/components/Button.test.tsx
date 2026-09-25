import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "@/components/ui";

describe("Button", () => {
  it("calls onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Get started free</Button>);

    await userEvent.click(screen.getByRole("button", { name: "Get started free" }));

    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not call onClick when disabled", async () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} disabled>
        Disabled
      </Button>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Disabled" }));

    expect(onClick).not.toHaveBeenCalled();
  });
});
