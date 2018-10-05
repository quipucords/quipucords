import React from 'react';
import { mount } from 'enzyme';
import SourcesEmptyState from '../sourcesEmptyState';

describe('SourcesEmptyState Component', () => {
  it('should render a basic component', () => {
    const props = {};
    const component = mount(<SourcesEmptyState {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
