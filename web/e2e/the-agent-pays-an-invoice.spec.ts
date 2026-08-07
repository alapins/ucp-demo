import { expect, test, type BrowserContext, type Page } from "@playwright/test";

/**
 * The demo's whole cycle, in the two windows a human watches it in: an Invoice is
 * raised, the Agent wakes, and the Invoice comes back settled.
 *
 * Unlike the merchant-window tests, these cannot invent a Payer of their own. The Agent
 * holds one API key and that key names one Payer, so the Invoice it is asked to pay must
 * be that Payer's — the Agent has no way to be shown anyone else's.
 */

const THE_PAYER_THE_AGENT_ACTS_FOR = "vampserv@gmail.com";

const rowFor = (page: Page, docNumber: string) =>
  page.getByTestId("invoice-list").locator("tr", { hasText: docNumber });

const logOf = (page: Page, type: string) =>
  page.getByTestId("event-log").locator("li", { hasText: type });

async function openBothWindows(page: Page, context: BrowserContext) {
  const merchantWindow = page;
  await merchantWindow.goto("/merchant");
  await expect(merchantWindow.locator(".connection")).toHaveText("live");

  const agentWindow = await context.newPage();
  await agentWindow.goto("/agent");
  await expect(agentWindow.locator(".connection")).toHaveText("live");

  return { merchantWindow, agentWindow };
}

test("an Invoice is discovered and paid without anybody pressing anything", async ({
  page,
  context,
  request,
}) => {
  const { merchantWindow, agentWindow } = await openBothWindows(page, context);

  // Raised through the Invoice API only so the test can read back the Doc Number the
  // Merchant minted and follow that one Invoice. Nothing is clicked in either window.
  const raised = await request.post("http://localhost:8080/invoices", {
    data: {
      payerEmail: THE_PAYER_THE_AGENT_ACTS_FOR,
      originalTotalMinorUnits: 51200,
      dueDate: "2099-03-28",
    },
  });
  const { docNumber } = await raised.json();

  // The Agent woke because the Invoice exists, not because a human asked.
  await expect(logOf(agentWindow, "agent.woke").first()).toBeVisible();
  await expect(logOf(agentWindow, "agent.decided").first()).toBeVisible();
  // It confirmed against the Merchant's own records rather than trusting the Checkout
  // it had just completed.
  await expect(logOf(agentWindow, "agent.payment_verified").first()).toBeVisible();

  // And the Merchant's own window shows it settled, reached by the event stream exactly
  // as a payment made by hand would be. Nothing in that window asked for it.
  await expect(rowFor(merchantWindow, docNumber)).toContainText("Paid");
  await expect(rowFor(merchantWindow, docNumber)).toContainText("$0.00");
});

test("Run Agent Now starts a run on demand", async ({ page, context }) => {
  const { agentWindow } = await openBothWindows(page, context);

  // The button is one of the Agent's four Wakes, not a test affordance, and it has to
  // keep working now that Invoices wake the Agent by themselves. What a run finds is
  // not this test's business — that it runs at all is.
  const runsBefore = await logOf(agentWindow, "agent.woke").count();

  await agentWindow.getByRole("button", { name: "Run Agent Now" }).click();

  await expect(logOf(agentWindow, "agent.woke")).toHaveCount(runsBefore + 1);
  await expect(logOf(agentWindow, "agent.finished")).toHaveCount(runsBefore + 1);
});

test("the merchant window never sees the Agent's reasoning", async ({
  page,
  context,
}) => {
  const { merchantWindow, agentWindow } = await openBothWindows(page, context);

  await agentWindow.getByRole("button", { name: "Run Agent Now" }).click();
  await expect(logOf(agentWindow, "agent.finished").first()).toBeVisible();

  // The trust boundary of ADR 0004: the Merchant is told about its own Invoices, and is
  // never told what the Payer's Agent thought about them.
  await expect(logOf(merchantWindow, "agent.")).toHaveCount(0);
});
