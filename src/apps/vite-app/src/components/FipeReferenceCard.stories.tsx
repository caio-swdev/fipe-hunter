import type { Meta, StoryObj } from '@storybook/react'
import { FipeReferenceCard } from './FipeReferenceCard'
import type { FipeReference } from './FipeReferenceCard'

const outlander: FipeReference = {
  brand: 'Mitsubishi',
  model: 'OUTLANDER 3.0/ GT 3.0 V6 Aut.',
  year: 2016,
  reference_price: 97420,
  fipe_code: '022101-5',
  reference_month: 'fevereiro de 2026',
}

const meta: Meta<typeof FipeReferenceCard> = {
  title: 'FIPE Hunter/FipeReferenceCard',
  component: FipeReferenceCard,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof FipeReferenceCard>

export const Default: Story = {
  args: { fipe: outlander },
}

export const BudgetCar: Story = {
  args: {
    fipe: {
      brand: 'Volkswagen',
      model: 'GOL 1.0 Flex',
      year: 2020,
      reference_price: 52800,
      fipe_code: '005340-8',
      reference_month: 'fevereiro de 2026',
    },
  },
}

export const LuxuryCar: Story = {
  args: {
    fipe: {
      brand: 'BMW',
      model: 'X5 xDrive50i 4.4 V8 Biturbo',
      year: 2022,
      reference_price: 498000,
      fipe_code: '010312-1',
      reference_month: 'fevereiro de 2026',
    },
  },
}
