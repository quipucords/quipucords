import React from 'react';
import PropTypes from 'prop-types';
import { Icon, ListView } from 'patternfly-react';

import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

const ListStatusItem = ({
  id,
  count,
  emptyText,
  tipSingular,
  tipPlural,
  expanded,
  expandType,
  toggleExpand,
  iconType,
  iconName
}) => {
  let renderExpandContent = (iconType, iconName, count, text) => {
    if (iconType && iconName) {
      return (
        <React.Fragment>
          <Icon className="list-view-compound-item-icon" type={iconType} name={iconName} />
          <strong>{count}</strong>
        </React.Fragment>
      );
    } else {
      return (
        <span>
          <strong>{count}</strong>
          {` ${text}`}
        </span>
      );
    }
  };

  if (count > 0) {
    return (
      <ListView.InfoItem className="list-view-info-item-icon-count">
        <SimpleTooltip id={`${id}_tip`} tooltip={`${count}  ${count === 1 ? tipSingular : tipPlural}`}>
          <ListView.Expand
            expanded={expanded}
            toggleExpanded={() => {
              toggleExpand(expandType);
            }}
          >
            {renderExpandContent(iconType, iconName, count, tipPlural)}
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>
    );
  }

  return (
    <ListView.InfoItem className="list-view-info-item-icon-count empty-count">
      <SimpleTooltip id={`${id}_tip`} tooltip={`0 ${tipPlural}`}>
        <span>{emptyText}</span>
      </SimpleTooltip>
    </ListView.InfoItem>
  );
};

ListStatusItem.propTypes = {
  id: PropTypes.string,
  count: PropTypes.number,
  emptyText: PropTypes.string,
  tipSingular: PropTypes.string,
  tipPlural: PropTypes.string,
  expanded: PropTypes.bool,
  expandType: PropTypes.string,
  toggleExpand: PropTypes.func,
  iconType: PropTypes.string,
  iconName: PropTypes.string
};

export default ListStatusItem;
