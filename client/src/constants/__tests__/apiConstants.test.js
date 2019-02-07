import apiTypes, * as allApiTypes from '../apiConstants';

describe('ApiTypes', () => {
  it('Should have specific API properties', () => {
    expect(apiTypes).toMatchSnapshot('specific types');

    expect(allApiTypes).toMatchSnapshot('all api types');
  });
});
