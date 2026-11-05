<?php
/** Execute the original PR's retry methods with deterministic transport/clock seams.
 * Usage: php tests/evals/retry-budget.php <ab-shop-checkout> <before-sha> <after-sha>
 * This tests the source behavior, not whether an LLM follows the review skill.
 */
declare(strict_types=1);

interface ResponseInterface {}
class TestResponse implements ResponseInterface {}
class RequestException extends RuntimeException {
    public function hasResponse(): bool { return false; }
}
class Transport {
    public int $calls = 0;
    public array $timeouts = [];
    public object $subject;
    public bool $fast = false;
    public function request(string $method, string $uri, array $options): ResponseInterface {
        $this->calls++;
        $this->timeouts[] = $options['timeout'];
        if ($this->fast && $this->calls === 2) { return new TestResponse(); }
        $this->subject->clock += $this->fast ? 0.5 : $options['timeout'];
        throw new RequestException('no response');
    }
}

if ($argc !== 4) { fwrite(STDERR, "Expected checkout, before SHA, after SHA\n"); exit(2); }
foreach (array_slice($argv, 2) as $index => $sha) {
    if (!preg_match('/^[a-f0-9]{40}$/', $sha)) { throw new RuntimeException('Use full SHAs'); }
    $cmd = 'git -C ' . escapeshellarg($argv[1]) . ' show ' . escapeshellarg($sha . ':modules/cp/lib/Base.php');
    exec($cmd, $lines, $exit);
    if ($exit !== 0) { throw new RuntimeException('Cannot read pinned source'); }
    $source = implode("\n", $lines);
    $lines = [];
    $start = strpos($source, '    private function requestWithTransportRetry(');
    $end = strpos($source, '    protected function pauseBeforeTransportRetry(', $start ?: 0);
    if ($start === false || $end === false) { throw new RuntimeException('Retry method boundaries missing'); }
    $method = substr($source, $start, $end - $start);
    if (!preg_match('/const TRANSPORT_RETRY_DELAYS_US = (\[[^;]+\]);/', $source, $delays)) {
        throw new RuntimeException('Retry delays missing');
    }
    $class = 'Subject' . $index;
    // Only the method and its real delays come from the pinned source. Time and
    // transport are controlled seams; no Guzzle, network, or wall-clock sleep.
    eval('class ' . $class . ' {
        const TRANSPORT_RETRY_DELAYS_US = ' . $delays[1] . ';
        public float $clock = 0;
        public Transport $client;
        protected function nowSeconds(): float { return $this->clock; }
        protected function pauseBeforeTransportRetry(int $us): void { $this->clock += $us / 1000000; }
        ' . $method . "\n}");
    foreach ([3.0, 60.0] as $budget) {
        foreach ([false, true] as $fast) {
            $subject = new $class();
            $transport = new Transport();
            $transport->subject = $subject;
            $transport->fast = $fast;
            $subject->client = $transport;
            $retryCount = 0;
            $args = ['GET', '/balance', ['timeout' => $budget], &$retryCount];
            $reflection = new ReflectionMethod($class, 'requestWithTransportRetry');
            if ($reflection->getNumberOfParameters() === 5) { $args[] = $budget; }
            try { $reflection->invokeArgs($subject, $args); } catch (RequestException $e) {}
            $expectedCalls = $fast ? 2 : ($index === 0 ? 3 : 1);
            $expectedTime = $fast ? 0.6 : ($index === 0 ? 3 * $budget + 0.4 : $budget);
            $expectedTimeout = $index === 1 && $fast ? $budget - 0.6 : $budget;
            if ($transport->calls !== $expectedCalls || abs($subject->clock - $expectedTime) > 1e-8
                || abs(end($transport->timeouts) - $expectedTimeout) > 1e-8) {
                throw new RuntimeException('Pinned retry behavior differs from expected before/after');
            }
            echo json_encode(['sha' => $sha, 'budget' => $budget, 'fast' => $fast,
                'calls' => $transport->calls, 'elapsed' => $subject->clock,
                'attempt_timeouts' => $transport->timeouts], JSON_THROW_ON_ERROR) . "\n";
        }
    }
}
