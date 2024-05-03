from __future__ import annotations

import asyncio
import contextlib
import io
import subprocess
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands
from discord.ext.commands import Paginator as CommandPaginator
from inspect import getsource
import os
import datetime
import random
import time
import aiohttp
import re
import json
import urllib


class TextPageSource:
    """ Get pages for text paginator """

    def __init__(self, text, *, prefix='```', suffix='```', max_size=2000, code_block=False):
        if code_block:
            prefix += "py\n"
        pages = CommandPaginator(
            prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split('\n'):
            if len(line) > 1789:
                for i in range(0, len(line), 1789):
                    pages.add_line(line[i:i + 1789])
            else:
                pages.add_line(line)

        self.pages = pages

    def get_pages(self, *, page_number=True):
        """ Gets the pages. """
        pages = []
        pagenum = 1
        for page in self.pages.pages:
            if page_number:
                page += f'\nPage {pagenum}/{len(self.pages.pages)}'
                pagenum += 1
            pages.append(page)
        return pages


class Restricted(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._last_result = None

    @commands.command(aliases=["eval"])
    @commands.is_owner()
    async def _eval(self, ctx, *, code):
        def clean_code(content):
            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:])[:-3]
            else:
                return content

        code = clean_code(code)

        local_variables = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "sauce": getsource,
            "os": os,
            "imp": __import__,
            "asyncio": asyncio,
            "datetime": datetime,
            "time": time,
            "random": random,
            "aiohttp": aiohttp,
            "re": re,
            "json": json,
            "urllib": urllib
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}", local_variables,
                )

                await local_variables["func"]()
                result = f"{stdout.getvalue()}\n"
        except Exception as e:
            result = "".join(traceback.format_exception(e, e, e.__traceback__))
        try:
            await ctx.send("```" + result[:2000] + "```")
        except Exception as e:
            await ctx.send(f"```{e}```")

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)
        return [output.decode() for output in result]

    @staticmethod
    def cleanup_code(content):
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')

    @commands.group(
        help="Developer tools.",
        brief="Dev tools.",
        aliases=['d', 'dev']
    )
    @commands.is_owner()
    async def developer(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Hmmm...", description=f"You seem lost. Try to use / for more commands.")
            await ctx.send(embed=embed)

    @developer.command(
        name='shell',
        help="Run something in shell.",
        brief="Run something in shell.",
        aliases=['sh']
    )
    async def developer_shell(self, ctx, *, command):
        async with ctx.typing():
            stdout, stderr = await self.run_process(command)

        if stderr:
            await ctx.message.add_reaction("❌")
            text = f'stdout:\n{stdout}\nstderr:\n{stderr}'
        else:
            await ctx.message.add_reaction("✅")
            text = stdout

        pages = TextPageSource(text).get_pages()

        for page in pages:
            await ctx.send(page)

    @developer.command(
        name='eval',
        help="Run something in python shell.",
        brief="Run something in python shell."
    )
    async def dev_eval(self, ctx, *, code: str):
        env = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "sauce": getsource,
            "os": os,
            "imp": __import__,
            "asyncio": asyncio,
            "datetime": datetime,
            "time": time,
            "random": random,
            "aiohttp": aiohttp,
            "re": re,
            "json": json,
            "urllib": urllib
        }

        env.update(globals())

        code = self.cleanup_code(code)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(code, "    ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            pages = TextPageSource(str(e.__class__.__name__) + ': ' + str(e), code_block=True).get_pages()
            if len(pages) == 1:
                await ctx.send(pages[0][:-8].strip())
            else:
                for page in pages:
                    await ctx.send(page)
            return

        else:
            func = env['func']

            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = stdout.getvalue()
                pages = TextPageSource(value + str("".join(traceback.format_exception(e, e, e.__traceback__))),
                                       code_block=True).get_pages()
                if len(pages) == 1:
                    await ctx.send(pages[0][:-8].strip())
                else:
                    for page in pages:
                        await ctx.send(page)
            else:
                value = stdout.getvalue()

                if ret is None and value != '':
                    pages = TextPageSource(value, code_block=True).get_pages()
                    if len(pages) == 1:
                        await ctx.send(pages[0][:-8].strip())
                    else:
                        for page in pages:
                            await ctx.send(page)
                    return
                else:
                    self._last_result = ret
                    if value != '' or ret != '':
                        pages = TextPageSource(value + str(ret), code_block=True).get_pages()
                        if len(pages) == 1:
                            await ctx.send(pages[0][:-8].strip())
                        else:
                            for page in pages:
                                await ctx.send(page)


    @developer.error
    async def dev_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            em = discord.Embed(
                title="Hmmm...", description="You don't have permission to use this command.")
            try:
                await ctx.send(embed=em)
            except discord.HTTPException:
                pass
        else:
            print("Error in developer.py")
            raise error


def setup(bot):
    bot.add_cog(Restricted(bot))
