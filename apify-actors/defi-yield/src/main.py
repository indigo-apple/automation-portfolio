"""Apify Actor: DeFi Stablecoin Yield Scanner (DefiLlama)"""
import asyncio

from apify import Actor

from . import logic


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        Actor.log.info('downloading DefiLlama pools')
        pools = logic.fetch_pools()
        rows = logic.scan(
            pools,
            min_tvl=float(inp.get('minTvlUsd', 10_000_000)),
            min_apy=float(inp.get('minApy', 5)),
            max_apy=float(inp.get('maxApy', 200)),
            stablecoin_only=bool(inp.get('stablecoinOnly', True)),
            chains=inp.get('chains') or None,
            projects=inp.get('projects') or None,
            exclude_il=bool(inp.get('excludeIl', True)),
            top=int(inp.get('topN', 100)),
        )
        for row in rows:
            await Actor.push_data(row)
        await Actor.set_value('SUMMARY', {'pools': len(pools), 'found': len(rows)})
        Actor.log.info(f'{len(rows)} pools matched out of {len(pools)}')


if __name__ == '__main__':
    asyncio.run(main())
