import type { DailyQualityResponse } from '../types'

function escapeCsv(value: string | number | null): string {
  const text = value === null ? '' : String(value)

  // Metinlerin Excel tarafından formül olarak çalıştırılmasını önler.
  const safeText =
    typeof value === 'string' && /^[=+\-@\t\r\n]/.test(text)
      ? `'${text}`
      : text

  return `"${safeText.replace(/"/g, '""')}"`
}

export function createDailyQualityCsv(
  data: DailyQualityResponse,
): string {
  const rows: (string | number | null)[][] = [
    [
      'Dataset',
      'Start date',
      'End date',
      'Timezone',
      'Date',
      'Evaluated',
      'Passed',
      'Warning',
      'Failed',
      'Issues',
      'Issue rate (%)',
    ],
    ...data.days.map(day => [
      data.prefix || 'All records',
      data.start_date,
      data.end_date,
      data.timezone,
      day.date,
      day.evaluated_count,
      day.passed_count,
      day.warning_count,
      day.failed_count,
      day.issue_count,
      day.issue_rate === null
        ? null
        : day.issue_rate.toFixed(2),
    ]),
  ]

  // UTF-8 BOM, Excel'de karakterlerin doğru açılmasına yardımcı olur.
  return '\uFEFF' + rows
    .map(row => row.map(escapeCsv).join(','))
    .join('\r\n')
}

export function downloadDailyQualityCsv(
  data: DailyQualityResponse,
): void {
  const blob = new Blob(
    [createDailyQualityCsv(data)],
    { type: 'text/csv;charset=utf-8;' },
  )

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  const dataset = (data.prefix || 'all-records')
    .replace(/[^a-zA-Z0-9_-]/g, '_')

  link.href = url
  link.download =
    `factorypulse-daily-quality-${dataset}` +
    `-${data.start_date}-${data.end_date}.csv`

  document.body.appendChild(link)

  try {
    link.click()
  } finally {
    link.remove()

    // Tarayıcı indirmeyi başlattıktan sonra geçici adresi temizler.
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}