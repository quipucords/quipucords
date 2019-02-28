import apiTypes, * as allTypes from '../apiConstants';

describe('ApiTypes', () => {
  it('Should have specific API properties', () => {
    expect(apiTypes).toMatchSnapshot('default export');

    expect(allTypes).toMatchSnapshot('all exports');
  });
});
