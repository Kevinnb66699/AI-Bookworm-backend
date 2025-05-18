import { EntityRepository, Repository } from 'typeorm';
import { TextRecitation } from '../entities/TextRecitation';

@EntityRepository(TextRecitation)
export class TextRecitationService extends Repository<TextRecitation> {
  async deleteText(id: number) {
    await this.delete(id);
  }

  async updateText(id: number, content: string) {
    const text = await this.findOne({ where: { id } });
    if (!text) {
      throw new Error('Text not found');
    }
    text.content = content;
    return await this.save(text);
  }
} 