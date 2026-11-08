"""Apify Actor: Polymarket Liquidity Rewards Scanner"""
import asyncio

from apify import Actor

from . import logic


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        Actor.log.info('scanning Polymarket gamma API')
        markets = logic.fetch_markets(pages=int(inp.get('pages', 5)))
        rows = logic.scan(
            markets,
            min_daily=float(inp.get('minDailyRewardUsd', 1)),
            max_spread=inp.get('maxSpreadCents'),
            min_liquidity=float(inp.get('minLiquidityUsd', 0)),
            top=int(inp.get('topN', 100)),
        )
        for row in rows:
            await Actor.push_data(row)
        await Actor.set_value('SUMMARY', {'markets': len(markets), 'rewarded': len(rows)})
        await Actor.log.info(f'{len(rows)} rewarded markets out of {len(markets)}')


if __name__ == '__main__':
    asyncio.run(main())
