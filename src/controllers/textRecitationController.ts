import { Context } from 'koa';
import textRecitationService from '../services/textRecitationService';

class TextRecitationController {
  async deleteText(ctx: Context) {
    const { id } = ctx.params;
    await textRecitationService.deleteText(Number(id));
    ctx.body = { success: true };
  },

  async updateText(ctx: Context) {
    const { id } = ctx.params;
    const { content } = ctx.request.body;
    const updatedText = await textRecitationService.updateText(Number(id), content);
    ctx.body = updatedText;
  },
}

export default new TextRecitationController(); 