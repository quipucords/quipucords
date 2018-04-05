import React from 'react';
import { mount } from 'enzyme';
import ListStatusItem from '../listStatusItem';

describe('ListStatusItem Component', function() {
  it('should render', () => {
    const props = {
      key: 'credential',
      id: 'credential',
      count: 100,
      emptyText: '0 Credentials',
      tipSingular: 'Credential',
      tipPlural: 'Credentials',
      expanded: true,
      expandType: 'credentials',
      toggleExpand: jest.fn(),
      iconInfo: { type: 'fa', name: 'id-card' }
    };

    const component = mount(<ListStatusItem {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
