import os
import discord
from discord.ext import commands
import aioredis
from typing import Any

from expiringdict import ExpiringDict

from aioredis_lock import LockTimeoutError, RedisLock
import structlog
import logging
import helpers
from helpers import checks

import aiohttp
import jishaku

dcogs=[
  "data.py",
  "redis.py",
  "mongo.py",
  "lang.py"
]

cogs=[
  "bot.py",
  "pokemon.py",
  "sprites.py",
  "config.py",
  "help.py",
  "battling.py",
  "market.py",
  "trading.py",
  "shop.py",
  "spawning.py",
  "auctions.py",
  "admin.py",
  "quest.py"
]

DEFAULT_DISABLED_MESSAGE = (
    "The bot's currently disabled. It may be refreshing for some quick updates, or down for another reason. "
    "Try again later and check the #bot-outages channel in the official server for more details."
)

CONCURRENCY_LIMITED_COMMANDS = {
    "auction",
    "market",
    "evolve",
    "favorite",
    "favoriteall",
    "nickall",
    "nickname",
    "reindex",
    "release",
    "releaseall",
    "select",
    "unfavorite",
    "unfavoriteall",
    "unmega",
    "buy",
    "dropitem",
    "embedcolor",
    "moveitem",
    "open",
    "redeemspawn",
    "trade",
    "learn",
    "halloween",
    "valentine",
    "spring",
    "pride",
}
class ClusterBot(commands.AutoShardedBot):
    class BlueEmbed(discord.Embed):
      def __init__(self, **kwargs):
          color = kwargs.pop("color", helpers.constants.BLUE)
          super().__init__(**kwargs, color=color)

    class Embed(discord.Embed):
      def __init__(self, **kwargs):
          color = kwargs.pop("color", helpers.constants.PINK)
          super().__init__(**kwargs, color=color)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs,intents=discord.Intents.all(),owner_ids=[750015265135263835, 887973552958087168],stripe_after_prefix=True)
        #self.mongo_cog = None  # Initialize to None
        self.activity = discord.Game(" .help • pokeverse")
        self.Pokeverse = "Pokeverse"
        self.cluster_name="Pokeverse2"
        self.cluster_idx = 0
        self.menus = ExpiringDict(max_len=300, max_age_seconds=300)
        self.add_check(
          commands.bot_has_permissions(
              read_messages=True,
              send_messages=True,
              embed_links=True,
              attach_files=True,
              read_message_history=True,
              add_reactions=True,
              external_emojis=True,
          ).predicate
        )

        self.add_check(checks.general_check().predicate)
        self.setup_logging()
  

    async def on_ready(self):
        db=os.getenv("redf")
        
        print(f"We have logged in as {self.user}")
        bot.remove_command("help")
        self.http_session = aiohttp.ClientSession()
        await bot.load_extension("jishaku")
        for filename in dcogs:
           if filename.endswith('.py'):
        
            await self.load_extension(f'cogz.{filename[:-3]}')
            print(f"Loaded {filename}")
        for filename in cogs:
           if filename.endswith('.py'):

            await self.load_extension(f'cogz.{filename[:-3]}')
            print(f"Loaded {filename}")
        
  # Set the Mongo cog reference
    def setup_logging(self):
      self.log: structlog.BoundLogger = structlog.get_logger()

      def add_cluster_name(logger, name, event_dict):
          event_dict["cluster"] = self.cluster_name
          return event_dict

      timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
      shared_processors = [structlog.stdlib.add_log_level, timestamper, add_cluster_name]

      structlog.configure(
          processors=[
              *shared_processors,
              structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
          ],
          logger_factory=structlog.stdlib.LoggerFactory(),
          cache_logger_on_first_use=True,
      )

      formatter = structlog.stdlib.ProcessorFormatter(
          # These run ONLY on `logging` entries that do NOT originate within
          # structlog.
          foreign_pre_chain=shared_processors,
          # These run on ALL entries after the pre_chain is done.
          processors=[
              # Remove _record & _from_structlog.
              structlog.stdlib.ProcessorFormatter.remove_processors_meta,
              structlog.dev.ConsoleRenderer() if True else structlog.processors.JSONRenderer(),
          ],
      )

      handler = logging.StreamHandler()
      handler.setFormatter(formatter)
      root_logger = logging.getLogger()
      root_logger.addHandler(handler)
      root_logger.setLevel(logging.INFO)
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore messages from other bots
        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        # Handle other errors as needed
        print(f"Error: {error}")

    async def get_context(self, message, *, cls=helpers.context.PoketwoContext):
      return await super().get_context(message, cls=cls)
      
    async def is_owner(self, user):
      if isinstance(user, discord.Member):
        if user.id in [750015265135263835, 887973552958087168]:
            return True
      return await super().is_owner(user)
    @property
    def mongo(self):
        """Returns the Mongo db from the 'Mongo' cog."""
        return self.get_cog("Mongo")
    @property
    def redis(self):
        """Returns the Redis pool from the 'Redis' cog."""
        return self.get_cog("Redis").pool

    @property
    def data(self):
        """Returns the data instance from the 'Data' cog."""
        return self.get_cog("Data").instance
    @property
    def lang(self):
        return self.get_cog("Lang").fluent
      
    @property
    def sprites(self):
        return self.get_cog("Sprites")


  
    async def send_dm(self, user, *args, **kwargs):
      if not isinstance(user, discord.abc.Snowflake):
          user = discord.Object(user)

      dm = await self.create_dm(user)
      return await dm.send(*args, **kwargs)
    async def on_message(self, message: discord.Message):
      message.content = message.content.replace("—", "--").replace("'", "′").replace("‘", "′").replace("’", "′")
      await self.process_commands(message)

    async def invoke(self, ctx):
      if ctx.command is None:
          return

      if not (
          ctx.command.name in CONCURRENCY_LIMITED_COMMANDS
          or (ctx.command.root_parent and ctx.command.root_parent.name in CONCURRENCY_LIMITED_COMMANDS)
      ):
          return await super().invoke(ctx)

      try:
          async with RedisLock(self.redis, f"command:{ctx.author.id}", 60, 1):
              return await super().invoke(ctx)
      except LockTimeoutError:
          await ctx.reply(ctx._("error-command-redis-locked"))

    async def close(self):
      self.log.info("close")
      await super().close()
      
    def _(self, message_id: str, **kwargs: Any) -> str:
      """Formats a localization string from a message ID."""
      # python-fluent expects a dict, but we accept message variables as
      # keyword arguments since it's more ergonomic.
      return self.lang.format_value(message_id, kwargs)


    def localized_embed(
      self,
      message_id: str,
      *,
      field_values: dict[str, Any] = {},
      droppable_fields: list[str] = [],
      ignored_fields: list[str] = [],
      field_ordering: list[str] = [],
      block_fields: list[str] | bool = False,
      **kwargs: Any,
    ) -> discord.Embed:
      """Creates an embed from localized message strings.

      This function looks up a Fluent message according to the passed ID, and
      applies the attributes of the message to the embed, formatting and
      passing along any keyword arguments as variables.

      If ``title``, ``description``, ``url``, or ``footer_text`` attributes
      are present, they are formatted and added to the embed.

      Embed fields may be specified through attributes with names in the format
      of ``field-[name]-name`` and ``field-[name]-value``. Both attributes
      must be present (unless the field value is overridden via ``field_values``,
      in which case the value attribute in Fluent can be omitted, or the field name
      is present in ``droppable_fields``, in which case the field is simply
      omitted from the embed altogether).

      Parameters
      ----------
      message_id
          The ID of the message in Fluent that contains the attributes
          describing the embed.
      field_values
          A dictionary of field names to field values. This allows the value
          attribute of a field to be absent in Fluent, granting full control
          of the field value to the calling code.
      droppable_fields
          A list of fields that may be silently dropped if their corresponding
          value in ``field_values`` is ``None`` or completely missing, or if
          a required attribute was simply not found. Normally, this would
          result in an error embed being returned.

          Use this parameter to be able to conditionally pass ``None`` values
          into ``field_values`` and have the field simply be omitted from the
          output.
      ignored_fields
          A list of field names that should be ignored. Can be used to
          conditionalize the presence of a field.
      field_ordering
          A list of field names that specifies the ordering in which fields
          should be added to the embed. If you specify this parameter, you
          must specify every field present in the message.
      block_fields
          A list of fields that are not inline ("block"). ``inline=False``
          will be passed into ``add_field`` for fields with their name in this
          list.

          You can also pass a boolean to determine the value passed to
          ``inline`` for all fields.
      **kwargs
          Variables to pass into all formatted messages.

      Raises
      ------
      ValueError
          If ``field_ordering`` is specified but a field name was missing.
      """

      error_title = self._("localization-error")
      error_embed = discord.Embed(color=discord.Color.red(), title=error_title)

      result = self.lang.get_message(message_id)
      if not result:
          self.log.error("no such message id", message_id=message_id)
          return error_embed

      msg, bundle = result
      attributes = msg.attributes

      embed = discord.Embed()

      PASSTHROUGH_FIELDS = ("title", "description", "url", "footer-text")
      for field in PASSTHROUGH_FIELDS:
        if field not in attributes:
            continue
        val, errors = bundle.format_pattern(attributes[field], kwargs)
        if errors:
            self.log.error(
                "failed to format passthrough field for localized embed",
                message_id=message_id,
                field=field,
                errors=errors,
            )
            return error_embed
        if field == "footer-text":
            embed.set_footer(text=val)
        else:
            setattr(embed, field, val)

      def format_field_attribute(*, field: str, key: str) -> str | None:
          key = f"field-{field}-{key}"

          try:
              title_message = attributes[key]
          except KeyError:
              return None

          val, errors = bundle.format_pattern(title_message, kwargs)

          if errors:
              return None
          return val

      def extract_field_name(fluent_attribute: str) -> str:
        return fluent_attribute[fluent_attribute.find("-") + 1 : fluent_attribute.rfind("-")]

      discovered_field_names = {
        name
        for key in attributes
        if key.startswith("field-") and (name := extract_field_name(key)) not in ignored_fields
      }
      if field_ordering:
        discovered_field_names = sorted(
            discovered_field_names, key=lambda field_name: field_ordering.index(field_name)
        )

      for field_name in discovered_field_names:
          name = format_field_attribute(field=field_name, key="name")
          # We aren't passing the default to `get` here because we want to fall
          # back even if the value is present, but `None`.
          value = field_values.get(field_name) or format_field_attribute(field=field_name, key="value")
          if not value:
            continue
          if name and value:
              if type(block_fields) is bool:
                  is_inline = not block_fields
              else:
                  is_inline = field_name not in block_fields
              embed.add_field(name=name, value=value, inline=is_inline)
          elif field_name not in droppable_fields:
              self.log.error(
                  "failed to format field attribute, and it isn't droppable",
                  message_id=message_id,
                  field_name=field_name,
              )
              return error_embed

      return embed

      

# Create an instance of the bot
bot = ClusterBot(command_prefix="!")

# Load cogs (e.g., MongoCog, etc.)
# bot.load_extension("cogs.mongo")

if __name__ == "__main__":
    bot.run("ODM0NTAwNDE3MDE0MDcxMzU2.Gyr5C2.1yDJDM2BGhVRf77PIF05VI7ubTyAV1HNXfgsOA")
    
