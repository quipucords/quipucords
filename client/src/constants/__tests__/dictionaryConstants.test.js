import dictionary, * as allTypes from '../dictionaryConstants';

describe('DictionaryTypes', () => {
  it('Should have specific Dictionary properties', () => {
    expect(dictionary).toMatchSnapshot('default export');

    expect(allTypes).toMatchSnapshot('all exports');
  });
});
