import React from 'react';
import PropTypes from 'prop-types';
import { Dropdown } from 'patternfly-react';
import _ from 'lodash';
import helpers from '../../common/helpers';

class DropdownSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = { dropdownIsOpen: false };
  }

  passOnClick = (event, callback) => {
    if (callback) {
      callback.apply(this, event);
    }

    this.toggleDropDown();
  };

  toggleDropDown = (a, b, c) => {
    const { dropdownIsOpen } = this.state;

    this.setState({
      dropdownIsOpen: (c && c.source === 'select') || !dropdownIsOpen
    });
  };

  render() {
    const { dropdownIsOpen } = this.state;
    const { id, title, multiselect, children } = this.props;
    const filteredProps = _.omit(this.props, ['multiselect']);

    if (!multiselect) {
      return (
        <Dropdown id={id || helpers.generateId()} {...filteredProps}>
          <Dropdown.Toggle>
            <span>{title}</span>
          </Dropdown.Toggle>
          <Dropdown.Menu>
            {children && React.Children.map(children, menuItem => React.cloneElement(menuItem))}
          </Dropdown.Menu>
        </Dropdown>
      );
    }

    return (
      <Dropdown id={id || helpers.generateId()} open={dropdownIsOpen} onToggle={this.toggleDropDown} {...filteredProps}>
        <Dropdown.Toggle>
          <span>{title}</span>
        </Dropdown.Toggle>
        <Dropdown.Menu>
          {children &&
            React.Children.map(children, menuItem =>
              React.cloneElement(menuItem, { onClick: e => this.passOnClick(e, menuItem.props.onClick) })
            )}
        </Dropdown.Menu>
      </Dropdown>
    );
  }
}

DropdownSelect.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string.isRequired,
  id: PropTypes.string,
  multiselect: PropTypes.bool
};

export { DropdownSelect as default, DropdownSelect };
