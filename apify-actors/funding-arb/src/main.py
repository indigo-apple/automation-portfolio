"""Apify Actor: Crypto Funding Rate Arbitrage Scanner"""
import asyncio

from apify import Actor

from . import logic


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        exchanges = inp.get('exchanges') or list(logic.FETCHERS)
        Actor.log.info(f'scanning {exchanges}')
        rows, errors, n_symbols = logic.scan(
            exchanges=exchanges,
            min_apr=float(inp.get('minAprPct', 10)),
            max_abs_rate_pct=float(inp.get('maxAbsRatePct', 0.5)),
            top=int(inp.get('topN', 50)),
        )
        if errors:
            Actor.log.warning(f'some exchanges failed: {errors}')
        for row in rows:
            await Actor.push_data(row)
        await Actor.set_value('SUMMARY', {'symbols': n_symbols, 'opportunities': len(rows), 'errors': errors})
        Actor.log.info(f'{n_symbols} symbols scanned, {len(rows)} opportunities')


if __name__ == '__main__':
    asyncio.run(main())
